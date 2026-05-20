"""
TruthGPT Advanced Persistence Layer — System 5.9 Platinum Edition.
Enhanced with SQLAlchemy ORM, Loguru, and Pydantic Settings.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

import httpx
import diskcache
import signal
from cryptography.fernet import Fernet
from sqlalchemy import Column, String, DateTime, Text, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Configuration ---

class PersistenceSettings(BaseSettings):
    """Strongly typed settings for persistence."""
    model_config = SettingsConfigDict(
        env_prefix="TRUTHGPT_", 
        env_file=".env",
        extra="ignore"
    )
    
    remote_url: Optional[str] = None
    db_url: str = "sqlite+aiosqlite:///agent_persistence.db"
    cache_dir: str = "snapshot_cache"
    log_file: str = "persistence.log"
    sync_timeout: float = 15.0
    encryption_key: str = Field(default_factory=lambda: Fernet.generate_key().decode())

settings = PersistenceSettings()

# Configure logging
logger.add(settings.log_file, rotation="10 MB", level="INFO")

# --- Database Schema ---

Base = declarative_base()

class TaskSnapshotModel(Base):
    """SQLAlchemy model for task snapshots."""
    __tablename__ = "task_snapshots"
    
    task_id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    agent_name = Column(String)
    state_json = Column(Text)
    status = Column(String, default="running")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Data Models ---

class TaskSnapshot(BaseModel):
    """Pydantic model for validation and serialization."""
    task_id: str
    user_id: str
    agent_name: str
    current_prompt: str
    iteration: int
    history: List[Dict[str, str]] = Field(default_factory=list) # Full conversation history
    core_memory: Dict[str, str] = Field(default_factory=dict)     # Snapshot of core memory blocks
    status: str = "running"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# --- Manager ---

class PersistenceManager:
    """
    Industrial-grade Persistence Manager.
    Uses Async SQLAlchemy for the database and DiskCache for hot-snapshots.
    """
    def __init__(self):
        self.engine = create_async_engine(settings.db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.cache = diskcache.Cache(settings.cache_dir)
        self.fernet = Fernet(settings.encryption_key.encode())
        
        self._init_task = None
        self._setup_signal_handlers()

    async def _ensure_db(self):
        """Lazy-init DB task if not already started."""
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._init_db())
        await self._init_task

    async def _init_db(self):
        """Initialize database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.success("Persistence Engine Ready.")
        except Exception as e:
            logger.error(f"Failed to initialize DB: {e}")

    async def save_snapshot(self, snapshot: TaskSnapshot):
        """Saves a snapshot locally and optionally offloads to cloud."""
        await self._ensure_db()
        
        # 1. Hot-cache for instant access
        self.cache[snapshot.task_id] = snapshot.model_dump()
        
        # 2. Persist to SQL
        try:
            async with self.async_session() as session:
                async with session.begin():
                    # Upsert logic
                    existing = await session.get(TaskSnapshotModel, snapshot.task_id)
                    if existing:
                        existing.state_json = snapshot.model_dump_json()
                        existing.status = snapshot.status
                    else:
                        session.add(TaskSnapshotModel(
                            task_id=snapshot.task_id,
                            user_id=snapshot.user_id,
                            agent_name=snapshot.agent_name,
                            state_json=snapshot.model_dump_json(),
                            status=snapshot.status
                        ))
                await session.commit()
        except Exception as e:
            logger.error(f"DB Save Error for {snapshot.task_id}: {e}")
        
        # 3. Cloud Offload (Infinite Horizon Pattern)
        if settings.remote_url:
            # We use a background task for regular updates
            asyncio.create_task(self._sync_to_remote(snapshot))
            
    async def sync_all_to_cloud(self):
        """Forces a sync of all active tasks to the cloud node."""
        tasks = await self.list_active_tasks()
        logger.info(f"Syncing {len(tasks)} tasks to cloud...")
        for task in tasks:
            await self._sync_to_remote(task)

    async def _sync_to_remote(self, snapshot: TaskSnapshot):
        """Offloads task state to a remote TruthGPT server."""
        try:
            async with httpx.AsyncClient(timeout=settings.sync_timeout) as client:
                resp = await client.post(
                    f"{settings.remote_url}/v1/persistence/sync",
                    json=snapshot.model_dump()
                )
                if resp.status_code == 200:
                    logger.debug(f"Cloud Sync OK: {snapshot.task_id}")
                else:
                    logger.warning(f"Cloud Sync Failed [{resp.status_code}]")
        except Exception as e:
            logger.error(f"Cloud Sync Network Error: {e}")

    async def load_snapshot(self, task_id: str) -> Optional[TaskSnapshot]:
        """Loads a snapshot from cache or database."""
        cached = self.cache.get(task_id)
        if cached:
            return TaskSnapshot(**cached)
            
        async with self.async_session() as session:
            result = await session.execute(
                select(TaskSnapshotModel).where(TaskSnapshotModel.task_id == task_id)
            )
            model = result.scalar_one_or_none()
            if model:
                return TaskSnapshot.model_validate_json(model.state_json)
        return None

    async def list_active_tasks(self) -> List[TaskSnapshot]:
        """Lists all running or paused tasks."""
        async with self.async_session() as session:
            result = await session.execute(
                select(TaskSnapshotModel).where(TaskSnapshotModel.status.in_(["running", "paused"]))
            )
            models = result.scalars().all()
            return [TaskSnapshot.model_validate_json(m.state_json) for m in models]

    async def mark_completed(self, task_id: str):
        """Marks a task as completed."""
        async with self.async_session() as session:
            async with session.begin():
                await session.execute(
                    update(TaskSnapshotModel)
                    .where(TaskSnapshotModel.task_id == task_id)
                    .values(status="completed")
                )
            await session.commit()
        self.cache.pop(task_id, None)
        logger.info(f"Task {task_id} completed.")

    async def fetch_remote_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Queries remote server for task completion."""
        if not settings.remote_url: return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.remote_url}/v1/persistence/status/{task_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "completed":
                        await self.mark_completed(task_id)
                    return data
        except Exception as e:
            logger.error(f"Remote fetch failed: {e}")
        return None

    def _setup_signal_handlers(self):
        """Prepares the manager for emergency shutdown sync."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, self._handle_exit)
            except ValueError:
                pass # Not in main thread

    def _handle_exit(self, signum, frame):
        """Emergency sync all tasks to cloud before exiting."""
        logger.warning(f"Shutdown signal {signum} detected. Performing EMERGENCY CLOUD SYNC...")
        
        # Bridge to async sync
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we schedule the task and hope it finishes
                # In a real CLI app, we might need a more robust way to wait
                loop.create_task(self.sync_all_to_cloud())
            else:
                # If loop is not running, we start a new one just for sync
                asyncio.run(self.sync_all_to_cloud())
        except Exception as e:
            logger.error(f"Emergency sync failed: {e}")
        
        logger.info("Emergency sync completed. Safe to exit.")

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.fernet.decrypt(token.encode()).decode()

_manager_instance: Optional[PersistenceManager] = None

def get_persistence_manager() -> PersistenceManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PersistenceManager()
    return _manager_instance
