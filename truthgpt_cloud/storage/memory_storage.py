"""
💾 TruthGPT Cloud - In-Memory Thread-Safe Storage Backend
Provides zero-disk-I/O persistence for isolated testing, ephemeral sessions, and unit testing.
"""

import copy
import threading
import time
from typing import Dict, Any, Optional

from .base import StorageBackend


class MemoryStorageBackend(StorageBackend):
    """
    In-memory StorageBackend implementation.
    Guarantees thread-safety and zero disk modifications.
    """

    def __init__(self, initial_data: Optional[Dict[str, Dict[str, Any]]] = None):
        self._lock = threading.RLock()
        self._data: Dict[str, Dict[str, Any]] = copy.deepcopy(initial_data) if initial_data else {}
        self.file_path = ":memory:"
        self.filepath = ":memory:"

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            col = self._data.get(collection, {})
            val = col.get(key)
            return copy.deepcopy(val) if val is not None else None

    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            if collection not in self._data:
                self._data[collection] = {}
            self._data[collection][key] = copy.deepcopy(value)

    def delete(self, collection: str, key: str) -> bool:
        with self._lock:
            if collection in self._data and key in self._data[collection]:
                del self._data[collection][key]
                return True
            return False

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            col = self._data.get(collection, {})
            return copy.deepcopy(col)

    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        with self._lock:
            self._data[collection] = copy.deepcopy(data)

    def create_snapshot(self) -> str:
        snapshot_id = f"mem_snap_{int(time.time() * 1000)}"
        return snapshot_id

    # Compatibility methods for AtomicJsonStorage interface
    def load(self) -> Dict[str, Any]:
        with self._lock:
            # Default to "subscriptions" collection if present, else root
            return copy.deepcopy(self._data.get("subscriptions", self._data))

    def save(self, data: Dict[str, Any]) -> bool:
        with self._lock:
            self._data["subscriptions"] = copy.deepcopy(data)
            return True


__all__ = ["MemoryStorageBackend"]
