"""
💾 TruthGPT Cloud - Storage Backend Abstract Interface
Defines the contract for persistent state engines (JSON, SQLite, Redis, PostgreSQL).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class StorageBackend(ABC):
    """Abstract interface for TruthGPT Cloud persistence."""

    @abstractmethod
    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key from a collection."""
        pass

    @abstractmethod
    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        """Store or update a record by key in a collection."""
        pass

    @abstractmethod
    def delete(self, collection: str, key: str) -> bool:
        """Delete a record by key."""
        pass

    @abstractmethod
    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all records from a collection."""
        pass

    @abstractmethod
    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        """Overwrite entire collection atomically."""
        pass

    @abstractmethod
    def create_snapshot(self) -> str:
        """Create a point-in-time snapshot/backup of storage."""
        pass


__all__ = ["StorageBackend"]
