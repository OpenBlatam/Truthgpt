"""
💾 TruthGPT Cloud - Storage Tiering & Migration Engine
Provides transactional data migration, cross-backend replication, and integrity verification
across JSON, SQLite, and In-Memory storage engines.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from .base import StorageBackend

logger = logging.getLogger("TruthGPT.StorageMigrator")


class StorageMigrationError(Exception):
    """Raised when data migration between storage backends fails."""
    pass


class StorageMigrator:
    """
    Manages data migration, consistency checks, and snapshot replication across storage engines.
    """

    @classmethod
    def migrate_collection(
        cls,
        source: StorageBackend,
        target: StorageBackend,
        collection: str,
        overwrite: bool = True,
    ) -> int:
        """
        Migrate all records in a collection from source to target storage backend.
        Returns the number of migrated records.
        """
        try:
            records = source.get_all(collection)
        except Exception as e:
            raise StorageMigrationError(f"Failed to read from source backend for collection '{collection}': {e}") from e

        if not records:
            return 0

        try:
            if overwrite:
                target.set_all(collection, records)
            else:
                for key, val in records.items():
                    if target.get(collection, key) is None:
                        target.set(collection, key, val)
            return len(records)
        except Exception as e:
            raise StorageMigrationError(f"Failed to write to target backend for collection '{collection}': {e}") from e

    @classmethod
    def validate_integrity(
        cls,
        source: StorageBackend,
        target: StorageBackend,
        collection: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate data integrity between source and target backends for a given collection.
        Returns (is_valid, report).
        """
        source_records = source.get_all(collection)
        target_records = target.get_all(collection)

        source_keys = set(source_records.keys())
        target_keys = set(target_records.keys())

        missing_in_target = list(source_keys - target_keys)
        extra_in_target = list(target_keys - source_keys)
        mismatched_keys = []

        for k in source_keys.intersection(target_keys):
            if source_records[k] != target_records[k]:
                mismatched_keys.append(k)

        is_valid = not (missing_in_target or extra_in_target or mismatched_keys)
        report = {
            "collection": collection,
            "source_record_count": len(source_records),
            "target_record_count": len(target_records),
            "missing_in_target_count": len(missing_in_target),
            "extra_in_target_count": len(extra_in_target),
            "mismatched_record_count": len(mismatched_keys),
            "is_valid": is_valid,
        }
        return is_valid, report

    @classmethod
    def sync_storage_backends(
        cls,
        primary: StorageBackend,
        secondary: StorageBackend,
        collections: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Synchronize multiple collections from primary to secondary storage backend.
        """
        cols = collections or ["subscriptions", "invoices", "audit_ledger", "webhooks"]
        migrated_counts: Dict[str, int] = {}
        for col in cols:
            count = cls.migrate_collection(primary, secondary, col, overwrite=True)
            migrated_counts[col] = count
        return migrated_counts

    @classmethod
    def export_snapshot(
        cls,
        backend: StorageBackend,
        output_json_path: str,
        collection: str = "subscriptions",
    ) -> str:
        """Export collection to a standalone formatted JSON snapshot file."""
        records = backend.get_all(collection)
        dir_name = os.path.dirname(os.path.abspath(output_json_path))
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return output_json_path

    @classmethod
    def import_snapshot(
        cls,
        backend: StorageBackend,
        input_json_path: str,
        collection: str = "subscriptions",
    ) -> int:
        """Import a JSON snapshot file into storage collection."""
        if not os.path.exists(input_json_path):
            raise FileNotFoundError(f"Snapshot file '{input_json_path}' not found.")
        with open(input_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Snapshot file must contain a JSON object mapping keys to records.")
        backend.set_all(collection, data)
        return len(data)


def sync_storage_backends(
    primary: StorageBackend,
    secondary: StorageBackend,
    collections: Optional[List[str]] = None,
) -> Dict[str, int]:
    """Helper function to sync collections across storage backends."""
    return StorageMigrator.sync_storage_backends(primary, secondary, collections)


__all__ = [
    "StorageMigrator",
    "StorageMigrationError",
    "sync_storage_backends",
]
