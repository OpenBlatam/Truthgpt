"""
SQLite-backed agent memory implementation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel

from optimization_core.agents.framework.memory.base import BaseMemory
from optimization_core.agents.framework.exceptions import MemoryPersistenceError

logger = logging.getLogger(__name__)


class PydanticEncoder(json.JSONEncoder):
    """Fallback encoder to safely serialize Pydantic instances inside dicts."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


_CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS chat_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT     NOT NULL,
    role      TEXT     NOT NULL,
    content   TEXT     NOT NULL,
    metadata  TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
_CREATE_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_user_id ON chat_history (user_id)"
)
_INSERT_SQL = (
    "INSERT INTO chat_history (user_id, role, content, metadata) "
    "VALUES (?, ?, ?, ?)"
)
_SELECT_SQL = """\
SELECT role, content, metadata, timestamp
  FROM chat_history
 WHERE user_id = ?
 ORDER BY id DESC
 LIMIT ?
"""

_DELETE_SQL = "DELETE FROM chat_history WHERE user_id = ?"
_COUNT_SQL = "SELECT COUNT(*) FROM chat_history WHERE user_id = ?"


class SQLiteMemory(BaseMemory):
    """
    Local memory implementation using SQLite partitioned by ``user_id``.
    Delegates thread blocking I/O to asyncio thread pool for zero latency.
    Configured with SQLite WAL mode for high concurrency.
    """

    def __init__(self, db_path: str | Path = "openclaw_memory.db") -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except sqlite3.Error as exc:
            logger.error("Database connection error on %s: %s", self.db_path, exc)
            raise MemoryPersistenceError(
                f"SQLite database error: {exc}",
                metadata={"db_path": str(self.db_path)},
            ) from exc
        finally:
            conn.close()

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL;")
                cur.execute("PRAGMA synchronous=NORMAL;")
                cur.execute(_CREATE_TABLE_SQL)
                cur.execute(_CREATE_INDEX_SQL)
                conn.commit()
            logger.info("Memoria SQLite inicializada en %s (WAL mode active)", self.db_path)
        except Exception as exc:
            logger.critical("Error al inicializar la base de datos: %s", exc)
            raise MemoryPersistenceError(
                f"Failed to initialize SQLite memory DB: {exc}",
                metadata={"db_path": str(self.db_path)},
            ) from exc

    # ------------------------------------------------------------------
    # Public async API (delegates to sync helpers via threads)
    # ------------------------------------------------------------------
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        await asyncio.to_thread(self._add_message_sync, user_id, role, content, metadata)

    async def get_history(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_history_sync, user_id, limit)

    async def clear_memory(self, user_id: str) -> None:
        await asyncio.to_thread(self._clear_memory_sync, user_id)

    async def bulk_insert_history(
        self, user_id: str, history: List[Dict[str, Any]]
    ) -> None:
        await asyncio.to_thread(self._bulk_insert_history_sync, user_id, history)

    async def count_messages(self, user_id: str) -> int:
        return await asyncio.to_thread(self._count_messages_sync, user_id)

    # ------------------------------------------------------------------
    # Synchronous helpers
    # ------------------------------------------------------------------
    def _add_message_sync(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            metadata_json = json.dumps(metadata, cls=PydanticEncoder) if metadata else None
            with self._get_connection() as conn:
                conn.cursor().execute(
                    _INSERT_SQL, (user_id, role, content, metadata_json)
                )
                conn.commit()
        except Exception as exc:
            logger.error("Error guardando mensaje para %s: %s", user_id, exc)

    def _get_history_sync(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                rows = conn.cursor().execute(_SELECT_SQL, (user_id, limit)).fetchall()

                history: List[Dict[str, Any]] = []
                for row in reversed(rows):  # chronological order
                    msg: Dict[str, Any] = {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                    }
                    raw_meta = row["metadata"]
                    if raw_meta:
                        try:
                            msg["metadata"] = json.loads(raw_meta)
                        except json.JSONDecodeError:
                            msg["metadata"] = {}
                    history.append(msg)
                return history
        except Exception as exc:
            logger.error("Error recuperando historial para %s: %s", user_id, exc)
            return []

    def _clear_memory_sync(self, user_id: str) -> None:
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(_DELETE_SQL, (user_id,))
                conn.commit()
        except Exception as exc:
            logger.error("Error limpiando memoria para %s: %s", user_id, exc)

    def _bulk_insert_history_sync(
        self, user_id: str, history: List[Dict[str, Any]]
    ) -> None:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                for msg in history:
                    metadata_json = json.dumps(msg.get("metadata"), cls=PydanticEncoder) if msg.get("metadata") else None
                    cur.execute(
                        _INSERT_SQL, (user_id, msg["role"], msg["content"], metadata_json)
                    )
                conn.commit()
        except Exception as exc:
            logger.error("Error en inserción masiva para %s: %s", user_id, exc)

    def _count_messages_sync(self, user_id: str) -> int:
        try:
            with self._get_connection() as conn:
                row = conn.cursor().execute(_COUNT_SQL, (user_id,)).fetchone()
                return int(row[0]) if row else 0
        except Exception as exc:
            logger.error("Error contando mensajes para %s: %s", user_id, exc)
            return 0


