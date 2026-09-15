"""
💾 TruthGPT Cloud - Atomic Persistent Storage
Provides crash-safe JSON serialization with atomic tempfile replacement,
optional high-speed orjson acceleration, and automatic recovery.
"""

import json
import os
import shutil
import tempfile
import threading
import time
import logging
from typing import Dict, Any, Optional
import uuid

from .base import StorageBackend

try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    _HAS_ORJSON = False

logger = logging.getLogger("TruthGPT.CloudStorage")


class AtomicJsonStorage(StorageBackend):
    """Thread-safe and process-safe atomic JSON file persistence with orjson acceleration."""

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self._lock = threading.RLock()
        self._ensure_parent_dir()

    @property
    def filepath(self) -> str:
        return self.file_path

    @filepath.setter
    def filepath(self, val: str) -> None:
        self.file_path = os.path.abspath(val)
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.file_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load JSON data from file or return empty dict on missing/corrupted file."""
        with self._lock:
            if not os.path.exists(self.file_path):
                return {}
            try:
                if _HAS_ORJSON:
                    with open(self.file_path, "rb") as f:
                        raw = f.read()
                        if not raw.strip():
                            return {}
                        data = orjson.loads(raw)
                        return data if isinstance(data, dict) else {}
                else:
                    with open(self.file_path, encoding="utf-8") as f:
                        data = json.load(f)
                        return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Failed to read storage file '{self.file_path}': {e}. Creating backup.")
                backup_path = f"{self.file_path}.corrupted_{os.getpid()}"
                try:
                    shutil.copyfile(self.file_path, backup_path)
                except Exception:
                    pass
                return {}

    def save(self, data: Dict[str, Any]) -> bool:
        """Write JSON data atomically using a temporary file with Windows file lock tolerance."""
        with self._lock:
            self._ensure_parent_dir()
            parent_dir = os.path.dirname(os.path.abspath(self.file_path))
            temp_fd, temp_path = tempfile.mkstemp(
                prefix="tgpt_sub_",
                suffix=".tmp",
                dir=parent_dir
            )
            try:
                if _HAS_ORJSON:
                    encoded = orjson.dumps(data, option=orjson.OPT_INDENT_2)
                    with open(temp_fd, "wb") as f:
                        f.write(encoded)
                else:
                    with open(temp_fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                # Atomic replace with retries for Windows file lock tolerance
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
                return True
            except Exception as e:
                logger.error(f"Failed to atomically write storage to '{self.file_path}': {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return False

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key from a collection."""
        data = self.load()
        if collection in data and isinstance(data[collection], dict):
            val = data[collection].get(key)
            return dict(val) if isinstance(val, dict) else val
        val = data.get(key)
        return dict(val) if isinstance(val, dict) else val

    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        """Store or update a record by key in a collection."""
        with self._lock:
            data = self.load()
            if collection in data and isinstance(data[collection], dict):
                data[collection][key] = value
            else:
                data[key] = value
            self.save(data)

    def delete(self, collection: str, key: str) -> bool:
        """Delete a record by key."""
        with self._lock:
            data = self.load()
            deleted = False
            if collection in data and isinstance(data[collection], dict) and key in data[collection]:
                del data[collection][key]
                deleted = True
            elif key in data:
                del data[key]
                deleted = True
            if deleted:
                self.save(data)
            return deleted

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all records from a collection."""
        data = self.load()
        if collection in data and isinstance(data[collection], dict):
            return dict(data[collection])
        return dict(data)

    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        """Overwrite entire collection atomically."""
        with self._lock:
            current = self.load()
            if collection in current and isinstance(current[collection], dict):
                current[collection] = data
                self.save(current)
            else:
                self.save(data)

    def create_snapshot(self) -> str:
        """Create a point-in-time snapshot/backup of storage."""
        with self._lock:
            self._ensure_parent_dir()
            ts = int(time.time())
            snap_path = f"{self.file_path}.snapshot_{ts}.json"
            if os.path.exists(self.file_path):
                shutil.copy2(self.file_path, snap_path)
            return snap_path


__all__ = [
    "AtomicJsonStorage",
    "_HAS_ORJSON",
]
