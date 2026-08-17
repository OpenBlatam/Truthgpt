"""
Cache Utilities for Core Data Management.
Provides hashing, key generation, and serialization helpers.
"""

import hashlib
import json
from typing import Any


class CacheUtils:
    """Helper utilities for cache operations."""

    @staticmethod
    def generate_key(prefix: str, data: Any) -> str:
        """Generate a deterministic cache key from input data."""
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True)
        else:
            serialized = str(data)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    @staticmethod
    def serialize_value(value: Any) -> bytes:
        """Serialize a python value to bytes."""
        if isinstance(value, bytes):
            return value
        return json.dumps(value).encode("utf-8")

    @staticmethod
    def deserialize_value(data: bytes) -> Any:
        """Deserialize bytes to a python object."""
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return data
