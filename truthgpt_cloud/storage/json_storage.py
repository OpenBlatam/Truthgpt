"""
💾 TruthGPT Cloud - Atomic Thread-Safe JSON Storage Backend
Provides durable storage with atomic writes, automatic backups, and thread safety.
"""

import os
import json
import time
import shutil
import tempfile
import threading
import logging
from typing import Dict, Any, Optional
from .base import StorageBackend

logger = logging.getLogger("TruthGPT.Storage.Json")


class JsonFileStorageBackend(StorageBackend):
    """
    Thread-safe, atomic JSON file storage with backup support and write debouncing.
    Debouncing prevents excessive disk I/O when rapid sequential writes occur.
    """

    def __init__(self, file_path: str, debounce_ms: int = 200):
        self.file_path = os.path.abspath(file_path)
        self._debounce_seconds = debounce_ms / 1000.0
        self._lock = threading.RLock()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self._flush_timer: Optional[threading.Timer] = None
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load state from disk with fallback to backup if main file corrupted."""
        with self._lock:
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self._memory_cache = data
                        return
                except Exception as e:
                    logger.warning(f"Error loading main storage file {self.file_path}: {e}. Checking backup...")
                    backup_path = f"{self.file_path}.bak"
                    if os.path.exists(backup_path):
                        try:
                            with open(backup_path, "r", encoding="utf-8") as bf:
                                data = json.load(bf)
                                if isinstance(data, dict):
                                    self._memory_cache = data
                                logger.info("Recovered storage state from backup file.")
                                return
                        except Exception as be:
                            logger.error(f"Failed to recover from backup file: {be}")
            self._memory_cache = {}

    def _schedule_flush(self) -> None:
        """Schedule a debounced flush to disk. Must be called with lock held."""
        self._dirty = True
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        self._flush_timer = threading.Timer(self._debounce_seconds, self._debounced_flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _debounced_flush(self) -> None:
        """Background flush callback invoked after debounce period."""
        with self._lock:
            if self._dirty:
                self._flush_to_disk()
                self._dirty = False

    def _flush_to_disk(self) -> None:
        """Atomically write memory cache to disk via temporary file with retry resilience."""
        dir_name = os.path.dirname(self.file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            prefix="tgpt_store_",
            suffix=".tmp",
            dir=dir_name
        )
        backup_path = f"{self.file_path}.bak"

        try:
            with open(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2, ensure_ascii=False)

            # Update backup if main file exists
            if os.path.exists(self.file_path):
                try:
                    shutil.copy2(self.file_path, backup_path)
                except Exception:
                    pass

            # Atomic replacement with retries for Windows file lock tolerance
            replaced = False
            for attempt in range(5):
                try:
                    os.replace(temp_path, self.file_path)
                    replaced = True
                    break
                except (PermissionError, OSError):
                    time.sleep(0.02 * (attempt + 1))

            if not replaced:
                shutil.move(temp_path, self.file_path)

        except Exception as e:
            logger.error(f"Error during atomic flush to {self.file_path}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    def flush_now(self) -> None:
        """Force an immediate flush to disk, bypassing debounce."""
        with self._lock:
            if self._flush_timer is not None:
                self._flush_timer.cancel()
                self._flush_timer = None
            self._flush_to_disk()
            self._dirty = False

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            col = self._memory_cache.get(collection, {})
            val = col.get(key)
            return dict(val) if isinstance(val, dict) else val

    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            if collection not in self._memory_cache:
                self._memory_cache[collection] = {}
            self._memory_cache[collection][key] = value
            self._schedule_flush()

    def delete(self, collection: str, key: str) -> bool:
        with self._lock:
            col = self._memory_cache.get(collection, {})
            if key in col:
                del col[key]
                self._schedule_flush()
                return True
            return False

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._memory_cache.get(collection, {}))

    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        with self._lock:
            self._memory_cache[collection] = data
            self._schedule_flush()

    def create_snapshot(self) -> str:
        with self._lock:
            self.flush_now()
            timestamp = int(time.time())
            snap_path = f"{self.file_path}.snapshot.{timestamp}.json"
            shutil.copy2(self.file_path, snap_path)
            return snap_path


__all__ = ["JsonFileStorageBackend"]
