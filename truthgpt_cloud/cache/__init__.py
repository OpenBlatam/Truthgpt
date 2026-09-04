"""
⚡ TruthGPT Cloud - Proof & Semantic Cache Subpackage
Exports cache interfaces, entries, and the singleton proof cache.
"""

from .base import BaseProofCache
from .redis_cache import RedisProofCacheBackend, _HAS_REDIS
from .proof_cache import (
    CachedProofEntry,
    CloudProofCache,
    proof_cache,
    _HAS_XXHASH,
    _HAS_ZSTD,
    _HAS_SIMSIMD,
)

__all__ = [
    "BaseProofCache",
    "CachedProofEntry",
    "CloudProofCache",
    "RedisProofCacheBackend",
    "proof_cache",
    "_HAS_XXHASH",
    "_HAS_ZSTD",
    "_HAS_REDIS",
    "_HAS_SIMSIMD",
]
