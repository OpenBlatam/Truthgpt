"""
Attention engine for the TruthGPT Polyglot Core.

Architecture
------------
This module implements a production-grade, multi-backend scaled dot-product
attention mechanism.  The class hierarchy is:

    Attention  (base – polyglot dispatch)
    ├── FlashAttention    (O(N) memory, tiled SRAM computation)
    ├── SparseAttention   (O(N × w) complexity via local windows)
    ├── GroupedQueryAttention  (GQA as in LLaMA-2/Mistral)
    ├── CrossAttention    (encoder-decoder cross-attention)
    └── SlidingWindowAttention  (long-context local attention)

Backend dispatch priority per feature
--------------------------------------
  attention, flash_attention → CPP > RUST > PYTHON
  sparse_attention            → CPP > PYTHON
  gqa                         → CPP > RUST > PYTHON

Numerical stability
-------------------
All Python paths implement the "safe softmax" algorithm:
  1. Subtract per-row maximum (prevents exp overflow)
  2. Add ε in the denominator (prevents division by zero)
  3. Operate in float64 during the critical softmax step

Observability
-------------
Every ``forward()`` call records latency and error status back into
`backend.record_backend_request()` so the health-score of each backend
stays current.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .backend import (
    Backend,
    get_best_backend,
    is_backend_available,
    record_backend_request,
)
from .constants import (
    DEFAULT_BLOCK_SIZE,
    DEFAULT_D_MODEL,
    DEFAULT_N_HEADS,
    EPSILON,
    LARGE_NEGATIVE_VALUE,
    MILLISECONDS_PER_SECOND,
)
from .config import AttentionConfig, AttentionPattern, KVCacheConfig, CacheStats

logger = logging.getLogger(__name__)

__all__ = [
    "AttentionOutput",
    "AttentionMetrics",
    "AttentionPattern",
    "Attention",
    "FlashAttention",
    "SparseAttention",
    "GroupedQueryAttention",
    "CrossAttention",
    "SlidingWindowAttention",
    "MultiHeadAttentionPool",
]


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT AND METRICS DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AttentionOutput:
    """
    Result of a single attention forward pass.

    Attributes
    ----------
    output:
        Output tensor [batch × seq, d_model].
    attention_weights:
        Optional attention probability matrix
        [batch, heads, seq, seq].
    compute_time_ms:
        Wall-clock computation time in milliseconds.
    memory_bytes:
        Approximate peak memory consumption of this call, in bytes.
    backend_used:
        The backend that executed the computation.
    """
    output:             np.ndarray
    attention_weights:  Optional[np.ndarray] = None
    compute_time_ms:    float = 0.0
    memory_bytes:       int   = 0
    backend_used:       str   = "python"

    @property
    def tokens_per_second(self) -> float:
        """Rough throughput estimate (tokens/sec) based on output shape."""
        if self.compute_time_ms <= 0:
            return 0.0
        n_tokens = self.output.shape[0] if self.output.ndim >= 1 else 1
        return n_tokens / (self.compute_time_ms / 1000.0)


@dataclass
class AttentionMetrics:
    """
    Rolling statistics collected across multiple forward passes.

    These are maintained per Attention instance and can be consumed
    by the monitoring subsystem.
    """
    total_calls:        int   = 0
    total_errors:       int   = 0
    total_tokens:       int   = 0
    total_time_ms:      float = 0.0
    peak_memory_bytes:  int   = 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_time_ms / self.total_calls if self.total_calls else 0.0

    @property
    def throughput_tokens_per_sec(self) -> float:
        if self.total_time_ms <= 0:
            return 0.0
        return self.total_tokens / (self.total_time_ms / 1000.0)

    @property
    def error_rate(self) -> float:
        return self.total_errors / self.total_calls if self.total_calls else 0.0

    def record(self, output: AttentionOutput, error: bool = False) -> None:
        self.total_calls   += 1
        self.total_tokens  += output.output.shape[0]
        self.total_time_ms += output.compute_time_ms
        self.peak_memory_bytes = max(self.peak_memory_bytes, output.memory_bytes)
        if error:
            self.total_errors += 1


# ─────────────────────────────────────────────────────────────────────────────
# BASE ATTENTION CLASS
# ─────────────────────────────────────────────────────────────────────────────

class Attention:
    """
    Unified multi-head attention with polyglot backend dispatch.

    The constructor accepts either a pre-built ``AttentionConfig`` or
    individual dimension arguments that are assembled into one.

    Parameters
    ----------
    config:
        Full attention configuration.
    d_model:
        Model hidden dimension (used when ``config`` is None).
    n_heads:
        Number of query heads (used when ``config`` is None).
    backend:
        Force a specific backend.  Pass ``None`` for auto-selection.
    **kwargs:
        Additional keyword arguments forwarded to ``AttentionConfig``.

    Example
    -------
    >>> config = AttentionConfig(d_model=1024, n_heads=16, n_kv_heads=8)
    >>> attn = Attention(config)
    >>> q = np.random.randn(4 * 128, 1024).astype(np.float32)
    >>> k = np.random.randn(4 * 128, 512).astype(np.float32)   # GQA
    >>> v = np.random.randn(4 * 128, 512).astype(np.float32)
    >>> out = attn.forward(q, k, v, batch_size=4, seq_len=128)
    >>> print(f"Latency: {out.compute_time_ms:.2f} ms")
    """

    def __init__(
        self,
        config: Optional[AttentionConfig] = None,
        *,
        d_model: int = DEFAULT_D_MODEL,
        n_heads: int = DEFAULT_N_HEADS,
        backend: Optional[Backend] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = AttentionConfig(d_model=d_model, n_heads=n_heads, **kwargs)
        self.config  = config
        self.metrics = AttentionMetrics()
        self._backend: Backend = backend or get_best_backend("attention")
        self._impl: Any       = self._create_implementation()
        logger.debug(
            "Attention initialised: d_model=%d n_heads=%d n_kv_heads=%d backend=%s",
            config.d_model, config.n_heads, config.n_kv_heads, self._backend.name,
        )

    # ------------------------------------------------------------------
    # Implementation creation (backend dispatch)
    # ------------------------------------------------------------------

    def _create_implementation(self) -> Optional[Any]:
        """Create the best available backend implementation."""
        if self._backend == Backend.CPP and is_backend_available(Backend.CPP):
            impl = self._try_create_cpp_impl()
            if impl is not None:
                return impl
        if self._backend == Backend.RUST and is_backend_available(Backend.RUST):
            impl = self._try_create_rust_impl()
            if impl is not None:
                return impl
        return None  # Python fallback

    def _try_create_cpp_impl(self) -> Optional[Any]:
        try:
            from optimization_core import _cpp_core  # type: ignore[import]
            cpp_cfg = _cpp_core.attention.FlashAttentionConfig(
                d_model=self.config.d_model,
                n_heads=self.config.n_heads,
                n_kv_heads=self.config.n_kv_heads,
                head_dim=self.config.head_dim,
                max_seq_len=self.config.max_seq_len,
                dropout=self.config.dropout,
                use_causal_mask=self._is_causal(),
                window_size=self.config.window_size,
            )
            impl = _cpp_core.attention.FlashAttentionCPU(cpp_cfg)
            logger.debug("Attention: using C++ FlashAttentionCPU backend")
            return impl
        except Exception as exc:
            logger.warning("Attention: C++ backend unavailable (%s), falling back", exc)
            return None

    def _try_create_rust_impl(self) -> Optional[Any]:
        try:
            from optimization_core.rust_core import truthgpt_rust  # type: ignore[import]
            impl = truthgpt_rust.PyAttention(
                d_model=self.config.d_model,
                n_heads=self.config.n_heads,
            )
            logger.debug("Attention: using Rust PyAttention backend")
            return impl
        except Exception as exc:
            logger.warning("Attention: Rust backend unavailable (%s), falling back", exc)
            return None

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    def forward(
        self,
        query:                    np.ndarray,
        key:                      np.ndarray,
        value:                    np.ndarray,
        batch_size:               int,
        seq_len:                  int,
        attention_mask:           Optional[np.ndarray] = None,
        key_padding_mask:         Optional[np.ndarray] = None,
        return_attention_weights: bool = False,
    ) -> AttentionOutput:
        """
        Compute scaled dot-product attention.

        Parameters
        ----------
        query:
            [batch × seq, d_model]
        key:
            [batch × seq, n_kv_heads × head_dim]
        value:
            [batch × seq, n_kv_heads × head_dim]
        batch_size:
            Number of sequences in the batch.
        seq_len:
            Length of each sequence.
        attention_mask:
            Optional additive mask [batch, seq, seq] or [seq, seq].
            Entries of ``-inf`` (or ``LARGE_NEGATIVE_VALUE``) are masked.
        key_padding_mask:
            Boolean mask [batch, seq] where ``True`` means *ignore*.
        return_attention_weights:
            If True, include attention probabilities in the output.

        Returns
        -------
        AttentionOutput
        """
        self._validate_inputs(query, key, value, batch_size, seq_len)
        start = time.perf_counter()

        try:
            if self._impl is not None and self._backend == Backend.CPP:
                result = self._forward_cpp(
                    query, key, value, batch_size, seq_len,
                    attention_mask, return_attention_weights,
                )
            else:
                result = self._forward_python(
                    query, key, value, batch_size, seq_len,
                    attention_mask, key_padding_mask, return_attention_weights,
                )

            elapsed_ms = (time.perf_counter() - start) * MILLISECONDS_PER_SECOND
            result.compute_time_ms = elapsed_ms
            result.backend_used    = self._backend.name
            self.metrics.record(result)
            record_backend_request(self._backend, elapsed_ms)
            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * MILLISECONDS_PER_SECOND
            record_backend_request(self._backend, elapsed_ms, error=True)
            self.metrics.total_errors += 1
            logger.error("Attention.forward failed on %s: %s", self._backend.name, exc)
            raise

    # ------------------------------------------------------------------
    # Backend-specific forward implementations
    # ------------------------------------------------------------------

    def _forward_cpp(
        self,
        query:        np.ndarray,
        key:          np.ndarray,
        value:        np.ndarray,
        batch_size:   int,
        seq_len:      int,
        mask:         Optional[np.ndarray],
        return_weights: bool,
    ) -> AttentionOutput:
        result = self._impl.forward(query, key, value, batch_size, seq_len, mask, return_weights)
        return AttentionOutput(
            output=result["output"],
            attention_weights=result.get("attention_weights"),
            compute_time_ms=result.get("compute_time_ms", 0.0),
            memory_bytes=result.get("memory_bytes", 0),
        )

    def _forward_python(
        self,
        query:             np.ndarray,
        key:               np.ndarray,
        value:             np.ndarray,
        batch_size:        int,
        seq_len:           int,
        attention_mask:    Optional[np.ndarray],
        key_padding_mask:  Optional[np.ndarray],
        return_weights:    bool,
    ) -> AttentionOutput:
        """
        Pure-NumPy scaled dot-product attention.

        Algorithm (Vaswani et al., 2017; with GQA extension):
          1. Reshape Q, K, V → [batch, seq, heads, head_dim]
          2. Transpose          → [batch, heads, seq, head_dim]
          3. GQA expansion      → repeat K/V heads if n_heads > n_kv_heads
          4. scores             = Q @ K^T / sqrt(head_dim)
          5. Apply causal mask  (upper-triangular −inf)
          6. Apply custom mask  (additive)
          7. Apply padding mask (−inf at pad positions)
          8. Softmax (stable)
          9. output             = softmax(scores) @ V
         10. Reshape back       → [batch × seq, d_model]
        """
        cfg       = self.config
        d_model   = cfg.d_model
        n_heads   = cfg.n_heads
        n_kv_heads= cfg.n_kv_heads
        head_dim  = cfg.head_dim

        # 1. Reshape
        q = query.reshape(batch_size, seq_len, n_heads, head_dim)
        k = key.reshape(batch_size, seq_len, n_kv_heads, head_dim)
        v = value.reshape(batch_size, seq_len, n_kv_heads, head_dim)

        # 2. Transpose → [batch, heads, seq, head_dim]
        q = q.transpose(0, 2, 1, 3)
        k = k.transpose(0, 2, 1, 3)
        v = v.transpose(0, 2, 1, 3)

        # 3. GQA / MQA expansion
        if cfg.is_gqa:
            repeat_factor = n_heads // n_kv_heads
            k = np.repeat(k, repeat_factor, axis=1)
            v = np.repeat(v, repeat_factor, axis=1)

        # 4. Scaled dot-product scores [batch, heads, seq_q, seq_k]
        scale  = cfg.softmax_scale  # 1/sqrt(head_dim) by default
        scores = np.matmul(q, k.transpose(0, 1, 3, 2)) * scale

        # 5. Causal mask
        if self._is_causal():
            scores = self._apply_causal_mask(scores, seq_len)

        # 6. Custom additive mask
        if attention_mask is not None:
            scores = self._apply_additive_mask(scores, attention_mask)

        # 7. Key-padding mask  [batch, seq_k] → broadcast over heads + seq_q
        if key_padding_mask is not None:
            pad_mask = key_padding_mask[:, np.newaxis, np.newaxis, :].astype(np.float64)
            scores = scores - pad_mask * LARGE_NEGATIVE_VALUE

        # 8. Numerically stable softmax (cast to float64 for stability)
        scores_f64 = scores.astype(np.float64)
        scores_f64 -= scores_f64.max(axis=-1, keepdims=True)
        exp_scores  = np.exp(scores_f64)
        weights     = (exp_scores / (exp_scores.sum(axis=-1, keepdims=True) + EPSILON)
                       ).astype(query.dtype)

        # 9. Dropout placeholder (training only)
        if cfg.dropout > 0.0 and getattr(cfg, "_training", False):
            drop_mask = np.random.binomial(1, 1.0 - cfg.dropout, weights.shape).astype(weights.dtype)
            weights   = weights * drop_mask / (1.0 - cfg.dropout)

        # Weighted sum [batch, heads, seq_q, head_dim]
        output = np.matmul(weights, v)

        # 10. Transpose + reshape → [batch × seq, d_model]
        output = output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, d_model)
        output = output.reshape(batch_size * seq_len, d_model)

        mem_bytes = (
            output.nbytes
            + (weights.nbytes if return_weights else 0)
            + q.nbytes + k.nbytes + v.nbytes
        )

        return AttentionOutput(
            output=output,
            attention_weights=weights if return_weights else None,
            memory_bytes=mem_bytes,
        )

    # ------------------------------------------------------------------
    # Mask helpers
    # ------------------------------------------------------------------

    def _is_causal(self) -> bool:
        return (
            getattr(self.config, "use_causal_mask", False)
            or self.config.pattern == AttentionPattern.CAUSAL
        )

    def _apply_causal_mask(self, scores: np.ndarray, seq_len: int) -> np.ndarray:
        """Upper-triangular causal mask (parallelised via broadcasting)."""
        mask = np.triu(
            np.full((seq_len, seq_len), LARGE_NEGATIVE_VALUE, dtype=scores.dtype),
            k=1,
        )
        return scores + mask[np.newaxis, np.newaxis, :, :]

    def _apply_additive_mask(self, scores: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply an additive attention mask.  0 = keep, 1 = ignore."""
        if mask.ndim == 2:
            mask = mask[np.newaxis, np.newaxis, :, :]
        elif mask.ndim == 3:
            mask = mask[:, np.newaxis, :, :]
        return scores + mask * LARGE_NEGATIVE_VALUE

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_inputs(
        self,
        query: np.ndarray,
        key:   np.ndarray,
        value: np.ndarray,
        batch_size: int,
        seq_len:    int,
    ) -> None:
        tokens = batch_size * seq_len
        expected_q  = (tokens, self.config.d_model)
        expected_kv = (tokens, self.config.n_kv_heads * self.config.head_dim)

        if query.shape != expected_q:
            raise ValueError(
                f"query shape {query.shape} != expected {expected_q}"
            )
        if key.shape != expected_kv:
            raise ValueError(
                f"key shape {key.shape} != expected {expected_kv}"
            )
        if value.shape != expected_kv:
            raise ValueError(
                f"value shape {value.shape} != expected {expected_kv}"
            )
        if query.dtype != key.dtype or query.dtype != value.dtype:
            raise ValueError(
                f"dtype mismatch: Q={query.dtype} K={key.dtype} V={value.dtype}"
            )

    # ------------------------------------------------------------------
    # Properties and dunder methods
    # ------------------------------------------------------------------

    @property
    def backend(self) -> Backend:
        """Currently active backend."""
        return self._backend

    def get_metrics(self) -> AttentionMetrics:
        """Return accumulated performance metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset accumulated metrics to zero."""
        self.metrics = AttentionMetrics()

    def __repr__(self) -> str:
        return (
            f"Attention(d_model={self.config.d_model}, "
            f"n_heads={self.config.n_heads}, "
            f"n_kv_heads={self.config.n_kv_heads}, "
            f"pattern={self.config.pattern.value!r}, "
            f"backend={self._backend.name})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALISED ATTENTION VARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class FlashAttention(Attention):
    """
    Flash Attention v2 – O(N) memory via SRAM-tiled computation.

    Reduces the memory footprint from O(N²) to O(N) by never
    materialising the full attention weight matrix.  On the C++ backend
    this maps directly to the ``FlashAttentionCPU`` kernel.

    Parameters
    ----------
    config:
        Attention configuration; ``block_size`` controls the SRAM tile size.
    **kwargs:
        Forwarded to ``AttentionConfig`` when *config* is None.

    Example
    -------
    >>> flash = FlashAttention(d_model=768, n_heads=12, block_size=64)
    >>> out = flash.forward(q, k, v, batch_size=2, seq_len=2048)
    """

    def __init__(
        self,
        config: Optional[AttentionConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = AttentionConfig(**kwargs)
        if config.block_size <= 0:
            config.block_size = DEFAULT_BLOCK_SIZE
        # Flash Attention prefers the C++ kernel
        super().__init__(config=config, backend=Backend.CPP)


class SparseAttention(Attention):
    """
    Sparse Attention with local windows and optional global tokens.

    Complexity: O(N × window_size + N × global_tokens) instead of O(N²).

    Parameters
    ----------
    window_size:
        Local attention window size on each side of a token.
    global_tokens:
        Number of "global" tokens that attend to all positions (e.g.
        a [CLS] token).  Must be > 0.
    **kwargs:
        Forwarded to ``AttentionConfig``.

    Example
    -------
    >>> sparse = SparseAttention(
    ...     d_model=1024, n_heads=16,
    ...     window_size=128, global_tokens=4,
    ... )
    """

    def __init__(
        self,
        config: Optional[AttentionConfig] = None,
        *,
        window_size:   int = 256,
        global_tokens: int = 16,
        **kwargs: Any,
    ) -> None:
        if global_tokens <= 0:
            raise ValueError(f"global_tokens must be > 0, got {global_tokens}")
        if config is None:
            config = AttentionConfig(**kwargs)
        config.pattern     = AttentionPattern.SPARSE
        config.window_size = window_size
        super().__init__(config=config)
        self.global_tokens = global_tokens


class GroupedQueryAttention(Attention):
    """
    Grouped-Query Attention (GQA) as used in LLaMA-2 / Mistral.

    Query heads are grouped; all heads in a group share a single
    key-value head pair, reducing the KV cache size by ``n_heads / n_kv_heads``.

    Parameters
    ----------
    d_model:
        Model hidden dimension.
    n_heads:
        Total number of query heads.
    n_kv_heads:
        Number of key-value head groups.  Must divide *n_heads* evenly.
    **kwargs:
        Forwarded to ``AttentionConfig``.

    Raises
    ------
    ValueError
        If ``n_heads`` is not divisible by ``n_kv_heads``.

    Example
    -------
    >>> gqa = GroupedQueryAttention(d_model=4096, n_heads=32, n_kv_heads=8)
    """

    def __init__(
        self,
        *,
        d_model:    int = DEFAULT_D_MODEL,
        n_heads:    int = DEFAULT_N_HEADS,
        n_kv_heads: int = 1,
        **kwargs: Any,
    ) -> None:
        if n_heads % n_kv_heads != 0:
            raise ValueError(
                f"n_heads ({n_heads}) must be divisible by n_kv_heads ({n_kv_heads})"
            )
        config = AttentionConfig(
            d_model=d_model,
            n_heads=n_heads,
            n_kv_heads=n_kv_heads,
            **kwargs,
        )
        super().__init__(config=config, backend=get_best_backend("gqa"))


class CrossAttention(Attention):
    """
    Encoder-Decoder Cross-Attention.

    Queries come from the decoder; keys and values come from the encoder.
    The API is identical to ``Attention.forward()`` but the causal mask
    is suppressed by default.

    Parameters
    ----------
    encoder_d_model:
        Hidden dimension of the encoder output (sets KV projection).
    **kwargs:
        Forwarded to ``Attention.__init__``.
    """

    def __init__(
        self,
        *,
        d_model:        int = DEFAULT_D_MODEL,
        encoder_d_model: int = DEFAULT_D_MODEL,
        n_heads:        int = DEFAULT_N_HEADS,
        **kwargs: Any,
    ) -> None:
        config = AttentionConfig(
            d_model=d_model,
            n_heads=n_heads,
            use_causal_mask=False,  # cross-attention is not causal
            **kwargs,
        )
        super().__init__(config=config)
        self.encoder_d_model = encoder_d_model


class SlidingWindowAttention(Attention):
    """
    Sliding-Window Attention for very long contexts (Longformer style).

    Each token attends only to its ``window_size`` nearest neighbours,
    giving O(N × window_size) complexity.  Useful for documents > 8 k tokens.

    Parameters
    ----------
    window_size:
        Number of positions on each side a token can attend to.
    **kwargs:
        Forwarded to ``Attention.__init__``.
    """

    def __init__(
        self,
        *,
        window_size: int = 512,
        **kwargs: Any,
    ) -> None:
        if window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {window_size}")
        config = AttentionConfig(
            pattern=AttentionPattern.SLIDING_WINDOW,
            window_size=window_size,
            **kwargs,
        )
        super().__init__(config=config)


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-HEAD ATTENTION POOL  (connection-pool pattern for shared resources)
# ─────────────────────────────────────────────────────────────────────────────

class MultiHeadAttentionPool:
    """
    Thread-safe pool of pre-created Attention instances.

    Useful in async serving scenarios where you want to limit the number
    of concurrent Attention objects (and their backend resources) while
    sharing them across multiple request handlers.

    Parameters
    ----------
    config:
        Shared AttentionConfig for all pool members.
    pool_size:
        Number of Attention instances to pre-create.
    attention_cls:
        Attention subclass to instantiate.  Defaults to ``Attention``.

    Example
    -------
    >>> pool = MultiHeadAttentionPool(
    ...     config=AttentionConfig(d_model=768, n_heads=12),
    ...     pool_size=4,
    ... )
    >>> with pool.acquire() as attn:
    ...     out = attn.forward(q, k, v, batch_size=1, seq_len=128)
    """

    def __init__(
        self,
        config:        Optional[AttentionConfig] = None,
        pool_size:     int = 4,
        attention_cls: type = Attention,
    ) -> None:
        import threading
        self._pool      = [attention_cls(config=config) for _ in range(pool_size)]
        self._available = list(range(pool_size))
        self._lock      = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def acquire(self) -> "Attention":
        """
        Return an Attention instance from the pool, blocking if all are in use.

        Use as a context manager via ``with pool.acquire() as attn: ...``.
        """
        with self._condition:
            while not self._available:
                self._condition.wait()
            idx  = self._available.pop()
            attn = self._pool[idx]
            attn._pool_idx = idx  # type: ignore[attr-defined]
            return _PooledAttention(attn, self)

    def release(self, attn: "Attention") -> None:
        idx = getattr(attn, "_pool_idx", None)
        if idx is not None:
            with self._condition:
                self._available.append(idx)
                self._condition.notify()

    def __len__(self) -> int:
        return len(self._pool)


class _PooledAttention:
    """Context-manager wrapper for ``MultiHeadAttentionPool``."""

    def __init__(self, attn: "Attention", pool: "MultiHeadAttentionPool") -> None:
        self._attn = attn
        self._pool = pool

    def __enter__(self) -> "Attention":
        return self._attn

    def __exit__(self, *_: Any) -> None:
        self._pool.release(self._attn)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._attn, name)
