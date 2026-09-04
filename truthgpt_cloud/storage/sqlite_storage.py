"""
💾 TruthGPT Cloud - ACID Transactional SQLite Storage Backend
Provides thread-safe relational persistence with WAL journal mode,
O(1) B-tree lookups, atomic multi-statement transactions, and JSON migration tools.
"""

import os
import time
import sqlite3
import threading
import logging
from typing import Dict, Any, Optional

try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    _HAS_ORJSON = False

from .base import StorageBackend

logger = logging.getLogger("TruthGPT.Storage.Sqlite")


def _encode_json(obj: Any) -> str:
    if _HAS_ORJSON:
        return orjson.dumps(obj).decode("utf-8")
    import json
    return json.dumps(obj, ensure_ascii=False)


def _decode_json(raw: str) -> Any:
    if _HAS_ORJSON:
        return orjson.loads(raw)
    import json
    return json.loads(raw)


class SqliteStorageBackend(StorageBackend):
    """
    ACID-compliant, high-concurrency SQLite storage engine for TruthGPT Cloud.
    Runs in WAL (Write-Ahead Logging) mode to enable non-blocking concurrent reads.
    """

    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self._lock = threading.RLock()
        self._ensure_parent_dir()
        self._init_db()

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kv_store (
                    collection TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (collection, key)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON kv_store(collection);")
            conn.commit()

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key from a collection."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value_json FROM kv_store WHERE collection = ? AND key = ?",
                (collection, key)
            )
            row = cursor.fetchone()
            if row:
                try:
                    return _decode_json(row[0])
                except Exception as e:
                    logger.error(f"Error decoding JSON for key '{key}': {e}")
                    return None
            return None

    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        """Store or update a record by key in a collection."""
        val_str = _encode_json(value)
        ts = time.time()
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT INTO kv_store (collection, key, value_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(collection, key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
            """, (collection, key, val_str, ts))
            conn.commit()

    def delete(self, collection: str, key: str) -> bool:
        """Delete a record by key from a collection."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM kv_store WHERE collection = ? AND key = ?",
                (collection, key)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all records from a collection."""
        results: Dict[str, Dict[str, Any]] = {}
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value_json FROM kv_store WHERE collection = ?",
                (collection,)
            )
            for k, val_str in cursor.fetchall():
                try:
                    results[k] = _decode_json(val_str)
                except Exception:
                    pass
        return results

    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        """Overwrite entire collection atomically inside a transaction."""
        ts = time.time()
        with self._lock, self._get_connection() as conn:
            conn.execute("DELETE FROM kv_store WHERE collection = ?", (collection,))
            for k, v in data.items():
                conn.execute(
                    "INSERT INTO kv_store (collection, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
                    (collection, k, _encode_json(v), ts)
                )
            conn.commit()

    def create_snapshot(self) -> str:
        """Create a point-in-time snapshot backup of the SQLite database."""
        with self._lock:
            ts = int(time.time())
            snap_path = f"{self.db_path}.snapshot_{ts}.db"
            # Use SQLite backup API for consistent point-in-time snapshot
            with self._get_connection() as src_conn:
                dest_conn = sqlite3.connect(snap_path)
                src_conn.backup(dest_conn)
                dest_conn.close()
            return snap_path

    def import_from_json(self, collection: str, json_file_path: str) -> int:
        """Import records from a JSON file into the specified SQLite collection."""
        if not os.path.exists(json_file_path):
            return 0
        with open(json_file_path, "rb") as f:
            raw = f.read()
            if not raw.strip():
                return 0
            data = _decode_json(raw.decode("utf-8") if not _HAS_ORJSON else raw)
        if not isinstance(data, dict):
            return 0
        self.set_all(collection, data)
        return len(data)

    def export_to_json(self, collection: str, json_file_path: str) -> int:
        """Export all records in collection to a formatted JSON file."""
        records = self.get_all(collection)
        dir_name = os.path.dirname(os.path.abspath(json_file_path))
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if _HAS_ORJSON:
            encoded = orjson.dumps(records, option=orjson.OPT_INDENT_2)
            with open(json_file_path, "wb") as f:
                f.write(encoded)
        else:
            import json
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        return len(records)


__all__ = ["SqliteStorageBackend"]
