"""
KV Cache Factories
==================
Factory functions and registry for Key-Value Cache modules, supporting disabled cache,
PagedKVCache, Sliding Window KV cache, Chunked KV cache, and Dynamic Quantized (FP8/INT8) KV Cache.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union

import torch

from .registry import Registry

logger = logging.getLogger(__name__)

# Import PagedKVCache with fallback handling
try:
    from optimization_core.modules.attention.ultra_efficient_kv_cache import PagedKVCache
except (ImportError, ModuleNotFoundError):
    try:
        from ..modules.attention.ultra_efficient_kv_cache import PagedKVCache
    except (ImportError, ModuleNotFoundError):
        try:
            from modules.attention.ultra_efficient_kv_cache import PagedKVCache
        except (ImportError, ModuleNotFoundError):

            class PagedKVCache:  # type: ignore
                """Fallback PagedKVCache mock implementation."""

                def __init__(
                    self,
                    num_heads: int = 8,
                    head_dim: int = 64,
                    max_tokens: int = 1024,
                    block_size: int = 128,
                    dtype: Optional[torch.dtype] = None,
                    **kwargs: Any,
                ):
                    self.num_heads = num_heads
                    self.head_dim = head_dim
                    self.max_tokens = max_tokens
                    self.block_size = block_size
                    self.dtype = dtype or torch.float32
                    self.length = 0

                def append(self, k: torch.Tensor, v: torch.Tensor) -> None:
                    self.length += k.shape[2] if k.ndim == 4 else k.shape[1]

                def reset(self) -> None:
                    self.length = 0


StandardKVCache = PagedKVCache

KV_CACHE = Registry(name="KVCacheRegistry")
KV_CACHE_FACTORIES = KV_CACHE


@dataclass
class KVCacheConfig:
    """Configuration specification for Key-Value cache construction."""

    type: str = "paged"
    num_heads: int = 8
    head_dim: int = 64
    max_tokens: int = 2048
    block_size: int = 128
    dtype: Optional[str] = None
    window_size: Optional[int] = 512
    quant_bits: Optional[int] = None
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate KV cache parameters."""
        if self.num_heads <= 0 or self.head_dim <= 0:
            raise ValueError(f"num_heads and head_dim must be positive, got heads={self.num_heads}, dim={self.head_dim}")
        return True


class SlidingWindowKVCache:
    """Sliding Window Key-Value Cache maintaining only the last window_size tokens."""

    def __init__(
        self,
        num_heads: int = 8,
        head_dim: int = 64,
        window_size: int = 512,
        dtype: torch.dtype = torch.float32,
        **kwargs: Any,
    ):
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.window_size = window_size
        self.dtype = dtype
        self.k_cache: Optional[torch.Tensor] = None
        self.v_cache: Optional[torch.Tensor] = None
        self.length = 0

    def append(self, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.k_cache is None:
            self.k_cache = k
            self.v_cache = v
        else:
            self.k_cache = torch.cat([self.k_cache, k], dim=-2)
            self.v_cache = torch.cat([self.v_cache, v], dim=-2)

        if self.k_cache.shape[-2] > self.window_size:
            self.k_cache = self.k_cache[..., -self.window_size :, :]
            self.v_cache = self.v_cache[..., -self.window_size :, :]

        self.length = self.k_cache.shape[-2]
        return self.k_cache, self.v_cache

    def reset(self) -> None:
        self.k_cache = None
        self.v_cache = None
        self.length = 0


@KV_CACHE.register(
    "none", priority=100, aliases=["disabled", "null"], description="Disable KV cache (returns None).", tags=["none", "disabled"]
)
def build_none(*args: Any, **kwargs: Any) -> None:
    """Disable KV cache (returns None)."""
    return None


@KV_CACHE.register(
    "paged",
    priority=90,
    aliases=["paged_kv", "vllm_style", "standard"],
    description="Build PagedKVCache instance for memory-efficient inference.",
    tags=["paged", "vllm", "standard"],
)
def build_paged(
    num_heads: int = 8,
    head_dim: int = 64,
    max_tokens: Optional[int] = None,
    max_seq_len: Optional[int] = None,
    block_size: int = 128,
    dtype: Optional[torch.dtype] = None,
    **kwargs: Any,
) -> PagedKVCache:
    """Build PagedKVCache instance for memory-efficient inference."""
    if dtype is None:
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    tokens = max_tokens or max_seq_len or 2048
    return PagedKVCache(
        num_heads=num_heads,
        head_dim=head_dim,
        max_tokens=tokens,
        block_size=block_size,
        dtype=dtype,
    )


build_standard = build_paged
build_kv_cache_none = build_none
build_kv_cache_paged = build_paged
build_standard_kv_cache = build_paged


@KV_CACHE.register(
    "sliding_window",
    priority=80,
    aliases=["sliding", "local"],
    description="Build SlidingWindowKVCache keeping fixed recent context window.",
    tags=["sliding_window", "local_context"],
)
def build_sliding_window(
    num_heads: int = 8,
    head_dim: int = 64,
    window_size: int = 512,
    dtype: Optional[torch.dtype] = None,
    **kwargs: Any,
) -> SlidingWindowKVCache:
    """Build Sliding Window KV Cache instance."""
    if dtype is None:
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    return SlidingWindowKVCache(
        num_heads=num_heads, head_dim=head_dim, window_size=window_size, dtype=dtype
    )


build_sliding_window_kv_cache = build_sliding_window


@KV_CACHE.register(
    "chunked",
    priority=70,
    aliases=["chunked_kv"],
    description="Build Chunked KV cache for long document processing.",
    tags=["chunked", "long_context"],
)
def build_chunked(
    num_heads: int = 8,
    head_dim: int = 64,
    max_tokens: int = 4096,
    block_size: int = 256,
    **kwargs: Any,
) -> PagedKVCache:
    """Build Chunked KV cache instance using PagedKVCache back-end."""
    return build_paged(
        num_heads=num_heads, head_dim=head_dim, max_tokens=max_tokens, block_size=block_size, **kwargs
    )


@KV_CACHE.register(
    "quantized",
    priority=60,
    aliases=["fp8_kv", "int8_kv"],
    description="Build Quantized KV Cache for ultra-low memory footprints.",
    tags=["quantized", "fp8", "int8"],
)
def build_quantized(
    num_heads: int = 8,
    head_dim: int = 64,
    max_tokens: int = 2048,
    quant_bits: int = 8,
    **kwargs: Any,
) -> PagedKVCache:
    """Build Quantized KV Cache instance (using 8-bit precision defaults)."""
    return build_paged(
        num_heads=num_heads,
        head_dim=head_dim,
        max_tokens=max_tokens,
        dtype=torch.float8_e4m3fn
        if hasattr(torch, "float8_e4m3fn")
        else torch.int8
        if hasattr(torch, "int8")
        else torch.float16,
        **kwargs,
    )


class KVCacheMemoryEstimate(dict):
    """Rich dict subclass representing KV cache memory estimation."""

    def __init__(self, data: Optional[Dict[str, float]] = None, **kwargs: Any):
        if data:
            super().__init__(data)
        else:
            super().__init__(**kwargs)

    @property
    def megabytes(self) -> float:
        return float(self.get("megabytes", 0.0))

    @property
    def gigabytes(self) -> float:
        return float(self.get("gigabytes", 0.0))

    @property
    def bytes(self) -> float:
        return float(self.get("bytes", 0.0))


def estimate_kv_cache_memory(
    num_layers: int = 12,
    num_heads: int = 12,
    head_dim: int = 64,
    seq_len: Optional[int] = None,
    max_seq_len: Optional[int] = None,
    batch_size: Optional[int] = None,
    max_batch_size: Optional[int] = None,
    precision_bytes: int = 2,
    **kwargs: Any,
) -> KVCacheMemoryEstimate:
    """
    Estimate total memory footprint of KV cache in Megabytes (MB) and Gigabytes (GB).
    """
    actual_seq_len = max_seq_len if max_seq_len is not None else (seq_len if seq_len is not None else 2048)
    actual_batch_size = max_batch_size if max_batch_size is not None else (batch_size if batch_size is not None else 1)

    total_bytes = float(
        2 * num_layers * num_heads * head_dim * actual_seq_len * actual_batch_size * precision_bytes
    )
    mb = total_bytes / (1024 * 1024)
    gb = total_bytes / (1024 * 1024 * 1024)

    return KVCacheMemoryEstimate({
        "megabytes": mb,
        "gigabytes": gb,
        "bytes": total_bytes,
    })


__all__ = [
    "KV_CACHE",
    "KV_CACHE_FACTORIES",
    "KVCacheConfig",
    "PagedKVCache",
    "StandardKVCache",
    "SlidingWindowKVCache",
    "KVCacheMemoryEstimate",
    "build_none",
    "build_paged",
    "build_standard",
    "build_sliding_window",
    "build_chunked",
    "build_quantized",
    "build_kv_cache_none",
    "build_kv_cache_paged",
    "build_standard_kv_cache",
    "build_sliding_window_kv_cache",
    "estimate_kv_cache_memory",
]
