"""
Data Cache Manager.
Provides in-memory caching with LRU policy and eviction control.
"""

from typing import Dict, Any, Optional
from collections import OrderedDict
import time
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """In-memory LRU cache."""

    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[float] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Get value by key, returning None if missing or expired."""
        if key not in self._cache:
            return None
        entry = self._cache[key]
        if self.ttl_seconds is not None:
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                del self._cache[key]
                return None
        self._cache.move_to_end(key)
        return entry["value"]

    def put(self, key: str, value: Any) -> None:
        """Put value into cache with eviction when full."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = {
            "value": value,
            "timestamp": time.time(),
        }
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all entries in cache."""
        self._cache.clear()

    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)


class CacheManager:
    """Central cache manager for managing multiple named DataCache pools."""

    _instance: Optional["CacheManager"] = None

    def __init__(self):
        self.pools: Dict[str, DataCache] = {}

    @classmethod
    def get_instance(cls) -> "CacheManager":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = CacheManager()
        return cls._instance

    def get_cache(self, name: str = "default", max_size: int = 1000, ttl_seconds: Optional[float] = None) -> DataCache:
        """Get or create named cache pool."""
        if name not in self.pools:
            self.pools[name] = DataCache(max_size=max_size, ttl_seconds=ttl_seconds)
        return self.pools[name]


def get_cache_manager() -> CacheManager:
    """Get global CacheManager instance."""
    return CacheManager.get_instance()

