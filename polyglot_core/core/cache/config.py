from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Union, Tuple
from collections import OrderedDict, deque
import numpy as np
import time
from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available

from .constants import *

class KVCacheConfig:
    """Configuration for KV Cache."""
    max_size: int = 100000
    max_memory_bytes: int = 8 * 1024 * 1024 * 1024  # 8GB
    eviction_strategy: EvictionStrategy = EvictionStrategy.LRU
    eviction_threshold: float = 0.85
    eviction_target: float = 0.70
    enable_compression: bool = True
    compression_threshold: int = 4096
    num_shards: int = 32
    
    @classmethod
    def inference_optimized(cls, memory_gb: int = 8) -> "KVCacheConfig":
        """Create config optimized for inference."""
        return cls(
            max_memory_bytes=memory_gb * 1024 * 1024 * 1024,
            eviction_strategy=EvictionStrategy.S3FIFO,
            enable_compression=True,
            num_shards=64
        )
    
    @classmethod
    def long_context(cls, memory_gb: int = 32) -> "KVCacheConfig":
        """Create config for long-context models."""
        return cls(
            max_memory_bytes=memory_gb * 1024 * 1024 * 1024,
            max_size=10_000_000,
            eviction_strategy=EvictionStrategy.ADAPTIVE,
            enable_compression=True,
            num_shards=128
        )

class CacheStats:
    """Cache performance statistics."""
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    entry_count: int = 0
    memory_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate

