"""
polyglot_core.domain.value_objects
====================================

Immutable, self-validating Value Objects for polyglot_core's domain layer.

Design principles
-----------------
* All VOs are frozen dataclasses – structural equality, hashable.
* Validation happens at ``__post_init__`` so invalid states are impossible.
* No imports from infrastructure, application, or presentation layers.
* Rich factory class-methods for common configurations.

Value Objects in this module
-----------------------------
TensorShape            – validated n-d tensor shape descriptor
ModelDimensions        – transformer architecture dimension bundle
BackendCapability      – feature bitmask for a single backend
BackendDescriptor      – immutable backend identity + capability snapshot
ComputeBudget          – max_latency + max_memory soft limits
LatencyBound           – SLA latency ceiling with jitter tolerance
MemoryBound            – memory ceiling with swap policy
QoSPolicy              – composite quality-of-service policy
SamplingParameters     – validated decoding / sampling hyper-parameters
TokenizerSpec          – tokenizer identity + special-token registry
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from enum import Enum, auto, unique
from typing import FrozenSet, Optional, Sequence, Tuple

from polyglot_core.domain.exceptions import (
    DimensionMismatchError,
    InvalidConfigurationError,
)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════════════


@unique
class BackendTag(str, Enum):
    """Symbolic backend identifiers."""

    PYTHON = "python"
    RUST = "rust"
    CPP = "cpp"
    GO = "go"
    JULIA = "julia"
    ELIXIR = "elixir"
    SCALA = "scala"

    @classmethod
    def from_string(cls, value: str) -> "BackendTag":
        """Case-insensitive lookup."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = [t.value for t in cls]
            raise InvalidConfigurationError(
                f"Unknown backend tag '{value}'. Valid values: {valid}"
            )


@unique
class EvictionPolicy(str, Enum):
    """KV-cache eviction algorithms."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    S3FIFO = "s3fifo"
    ARC = "arc"
    ADAPTIVE = "adaptive"
    NONE = "none"


@unique
class AttentionVariant(str, Enum):
    """Attention computation variants."""

    STANDARD = "standard"
    FLASH = "flash"
    SPARSE = "sparse"
    LINEAR = "linear"
    SLIDING_WINDOW = "sliding_window"
    GROUPED_QUERY = "grouped_query"


@unique
class PrecisionMode(str, Enum):
    """Numeric precision for computation."""

    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    MIXED = "mixed"


# ══════════════════════════════════════════════════════════════════════════════
# TENSOR SHAPE
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class TensorShape:
    """
    Immutable n-dimensional tensor shape with symbolic dimension names.

    Attributes
    ----------
    dims : tuple[int, ...]
        Non-negative dimension sizes. Use ``-1`` for dynamic / unknown dims.
    names : tuple[str, ...]
        Optional symbolic names, one per dimension.

    Example
    -------
    >>> shape = TensorShape((32, 512, 768), names=("batch", "seq", "d_model"))
    >>> shape.rank
    3
    >>> shape.num_elements
    12_582_912
    >>> shape[1]
    512
    """

    dims: Tuple[int, ...]
    names: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.dims:
            raise InvalidConfigurationError(
                "TensorShape requires at least one dimension"
            )
        for i, d in enumerate(self.dims):
            if d < -1:
                raise InvalidConfigurationError(
                    f"Dimension [{i}] must be >= -1 (use -1 for dynamic), got {d}"
                )
        if self.names and len(self.names) != len(self.dims):
            raise InvalidConfigurationError(
                f"len(names)={len(self.names)} must equal len(dims)={len(self.dims)}"
            )

    # ── convenience ────────────────────────────────────────────────────────

    @property
    def rank(self) -> int:
        """Number of dimensions."""
        return len(self.dims)

    @property
    def num_elements(self) -> int:
        """Total element count. Returns -1 if any dimension is dynamic."""
        if any(d < 0 for d in self.dims):
            return -1
        result = 1
        for d in self.dims:
            result *= d
        return result

    @property
    def is_dynamic(self) -> bool:
        """True if any dimension is not statically known."""
        return any(d < 0 for d in self.dims)

    def __getitem__(self, index: int) -> int:
        return self.dims[index]

    def __len__(self) -> int:
        return len(self.dims)

    def reshape_compatible(self, other: "TensorShape") -> bool:
        """Return True if ``self`` and ``other`` have the same element count."""
        return self.num_elements == other.num_elements

    @classmethod
    def batch_seq(cls, batch: int, seq: int) -> "TensorShape":
        return cls((batch, seq), names=("batch", "seq"))

    @classmethod
    def batch_seq_model(cls, batch: int, seq: int, d_model: int) -> "TensorShape":
        return cls((batch, seq, d_model), names=("batch", "seq", "d_model"))

    @classmethod
    def attn_heads(
        cls, batch: int, heads: int, seq: int, head_dim: int
    ) -> "TensorShape":
        return cls(
            (batch, heads, seq, head_dim),
            names=("batch", "heads", "seq", "head_dim"),
        )

    def __repr__(self) -> str:
        if self.names:
            parts = [f"{n}={d}" for n, d in zip(self.names, self.dims)]
        else:
            parts = [str(d) for d in self.dims]
        return f"TensorShape({', '.join(parts)})"


# ══════════════════════════════════════════════════════════════════════════════
# MODEL DIMENSIONS
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ModelDimensions:
    """
    Complete architectural dimension specification for a transformer model.

    All fields are validated for internal consistency (e.g., ``n_heads``
    must evenly divide ``d_model``).

    Attributes
    ----------
    d_model : int
        Hidden / embedding dimension.
    n_heads : int
        Number of query attention heads.
    n_kv_heads : int
        Number of key/value heads (1 = MHA, n_heads = MHA; < n_heads = GQA).
    d_ff : int
        Feed-forward intermediate dimension (typically 4× d_model).
    n_layers : int
        Number of transformer blocks.
    vocab_size : int
        Vocabulary size.
    max_seq_len : int
        Maximum supported context window.
    head_dim : int
        Per-head dimension (computed from d_model / n_heads if 0).
    rope_theta : float
        RoPE base frequency. Ignored for models without rotary embeddings.
    """

    d_model: int
    n_heads: int
    n_kv_heads: int
    d_ff: int
    n_layers: int
    vocab_size: int
    max_seq_len: int
    head_dim: int = 0  # auto-computed below
    rope_theta: float = 10_000.0

    def __post_init__(self) -> None:
        # Compute head_dim if not supplied
        if self.head_dim == 0:
            object.__setattr__(self, "head_dim", self.d_model // self.n_heads)

        # --- invariants ---
        if self.d_model <= 0:
            raise InvalidConfigurationError(
                "d_model must be positive", context={"d_model": self.d_model}
            )
        if self.n_heads <= 0:
            raise InvalidConfigurationError(
                "n_heads must be positive", context={"n_heads": self.n_heads}
            )
        if self.d_model % self.n_heads != 0:
            raise InvalidConfigurationError(
                "n_heads must evenly divide d_model",
                context={"d_model": self.d_model, "n_heads": self.n_heads},
            )
        if self.n_kv_heads <= 0 or self.n_heads % self.n_kv_heads != 0:
            raise InvalidConfigurationError(
                "n_kv_heads must be a positive divisor of n_heads",
                context={"n_heads": self.n_heads, "n_kv_heads": self.n_kv_heads},
            )
        if self.max_seq_len <= 0:
            raise InvalidConfigurationError(
                "max_seq_len must be positive",
                context={"max_seq_len": self.max_seq_len},
            )
        if self.vocab_size <= 0:
            raise InvalidConfigurationError(
                "vocab_size must be positive",
                context={"vocab_size": self.vocab_size},
            )

    # ── derived helpers ────────────────────────────────────────────────────

    @property
    def is_gqa(self) -> bool:
        """True when using Grouped-Query Attention (n_kv_heads < n_heads)."""
        return self.n_kv_heads < self.n_heads

    @property
    def gqa_ratio(self) -> int:
        """Number of query heads per KV head."""
        return self.n_heads // self.n_kv_heads

    @property
    def kv_dim(self) -> int:
        """Size of the KV projection (n_kv_heads × head_dim)."""
        return self.n_kv_heads * self.head_dim

    @property
    def parameter_count_estimate(self) -> int:
        """
        Approximate parameter count (embeddings + attention + FFN).

        Note: This is an order-of-magnitude estimate; actual counts vary
        by implementation (bias, normalisation layers, etc.).
        """
        embed = self.vocab_size * self.d_model
        attn_per_layer = (
            self.d_model * self.d_model           # Q
            + self.kv_dim * self.d_model * 2      # K + V
            + self.d_model * self.d_model          # O
        )
        ff_per_layer = 2 * self.d_model * self.d_ff
        return embed + self.n_layers * (attn_per_layer + ff_per_layer)

    @property
    def kv_cache_bytes_per_token(self) -> int:
        """
        Memory in bytes for a single token's KV state across all layers.

        Assumes float32 (4 bytes) storage.
        """
        bytes_per_element = 4  # float32
        return 2 * self.n_kv_heads * self.head_dim * self.n_layers * bytes_per_element

    # ── factories ─────────────────────────────────────────────────────────

    @classmethod
    def gpt2_small(cls) -> "ModelDimensions":
        """GPT-2 small (117M)."""
        return cls(
            d_model=768, n_heads=12, n_kv_heads=12,
            d_ff=3072, n_layers=12, vocab_size=50_257, max_seq_len=1024,
        )

    @classmethod
    def llama3_8b(cls) -> "ModelDimensions":
        """LLaMA-3 8B dimensions."""
        return cls(
            d_model=4096, n_heads=32, n_kv_heads=8,
            d_ff=14_336, n_layers=32, vocab_size=128_256, max_seq_len=8192,
            rope_theta=500_000.0,
        )

    @classmethod
    def llama3_70b(cls) -> "ModelDimensions":
        """LLaMA-3 70B dimensions."""
        return cls(
            d_model=8192, n_heads=64, n_kv_heads=8,
            d_ff=28_672, n_layers=80, vocab_size=128_256, max_seq_len=8192,
            rope_theta=500_000.0,
        )

    def __repr__(self) -> str:
        return (
            f"ModelDimensions("
            f"d_model={self.d_model}, n_heads={self.n_heads}, "
            f"n_kv_heads={self.n_kv_heads}, n_layers={self.n_layers}, "
            f"vocab={self.vocab_size}, max_seq={self.max_seq_len}"
            f"{'[GQA]' if self.is_gqa else ''})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND CAPABILITY & DESCRIPTOR
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class BackendCapability:
    """
    Immutable feature-set snapshot for a single backend.

    All attributes are boolean flags grouped into capability categories.

    Attributes
    ----------
    has_attention        : bool  – can perform attention computation
    has_flash_attention  : bool  – supports memory-efficient flash attention
    has_kv_cache         : bool  – has KV-cache management
    has_compression      : bool  – supports tensor compression
    has_tokenization     : bool  – provides tokenization primitives
    has_quantization     : bool  – supports INT8/INT4 quantization
    has_cuda             : bool  – GPU (CUDA) acceleration available
    has_distributed      : bool  – supports distributed multi-node ops
    has_streaming        : bool  – can stream tokens to clients
    performance_tier     : int   – 0=Python, 1=Rust, 2=C++, 3=C++/CUDA
    """

    has_attention: bool = False
    has_flash_attention: bool = False
    has_kv_cache: bool = False
    has_compression: bool = False
    has_tokenization: bool = False
    has_quantization: bool = False
    has_cuda: bool = False
    has_distributed: bool = False
    has_streaming: bool = False
    performance_tier: int = 0  # 0 = slowest (Python)

    def __post_init__(self) -> None:
        if not (0 <= self.performance_tier <= 3):
            raise InvalidConfigurationError(
                "performance_tier must be in [0, 3]",
                context={"performance_tier": self.performance_tier},
            )
        if self.has_flash_attention and not self.has_attention:
            raise InvalidConfigurationError(
                "has_flash_attention requires has_attention=True"
            )

    def supports(self, feature: str) -> bool:
        """Dynamic feature lookup by string name."""
        attr = f"has_{feature.replace('-', '_').lower()}"
        return getattr(self, attr, False)

    @classmethod
    def python_fallback(cls) -> "BackendCapability":
        """Pure Python (always available)."""
        return cls(
            has_attention=True,
            has_kv_cache=True,
            has_compression=True,
            has_tokenization=True,
            has_quantization=True,
            has_streaming=True,
            performance_tier=0,
        )

    @classmethod
    def rust_standard(cls) -> "BackendCapability":
        """Rust without GPU."""
        return cls(
            has_attention=True,
            has_kv_cache=True,
            has_compression=True,
            has_tokenization=True,
            has_quantization=True,
            has_streaming=True,
            performance_tier=1,
        )

    @classmethod
    def cpp_cpu(cls) -> "BackendCapability":
        """C++ with Eigen / SIMD (no GPU)."""
        return cls(
            has_attention=True,
            has_flash_attention=True,
            has_kv_cache=True,
            has_compression=True,
            has_quantization=True,
            has_streaming=True,
            performance_tier=2,
        )

    @classmethod
    def cpp_cuda(cls) -> "BackendCapability":
        """C++ with CUDA (GPU)."""
        return cls(
            has_attention=True,
            has_flash_attention=True,
            has_kv_cache=True,
            has_compression=True,
            has_quantization=True,
            has_streaming=True,
            has_cuda=True,
            performance_tier=3,
        )


@dataclass(frozen=True)
class BackendDescriptor:
    """
    Immutable identity + capability snapshot for a backend node.

    Attributes
    ----------
    tag          : BackendTag     – backend type enum
    version      : str            – semantic version string
    capability   : BackendCapability
    endpoint     : str | None     – URL for remote backends (Go, gRPC)
    performance_multiplier : float – relative speed vs Python baseline
    """

    tag: BackendTag
    version: str
    capability: BackendCapability
    endpoint: Optional[str] = None
    performance_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.performance_multiplier <= 0:
            raise InvalidConfigurationError(
                "performance_multiplier must be > 0",
                context={"multiplier": self.performance_multiplier},
            )

    def is_remote(self) -> bool:
        """True for backends accessed over a network."""
        return self.endpoint is not None

    def __repr__(self) -> str:
        remote = f", endpoint={self.endpoint!r}" if self.is_remote() else ""
        return (
            f"BackendDescriptor("
            f"tag={self.tag.value!r}, v{self.version}, "
            f"perf={self.performance_multiplier:.1f}x"
            f"{remote})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# COMPUTE BUDGET / QoS
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class LatencyBound:
    """
    Latency SLA ceiling with jitter tolerance.

    Parameters
    ----------
    p99_ms : float
        99th-percentile latency ceiling in milliseconds.
    jitter_tolerance_pct : float
        Allowable over-run percentage before raising an alarm (default 20%).

    Example
    -------
    >>> lb = LatencyBound(p99_ms=100.0)
    >>> lb.is_within_budget(95.0)   # True
    >>> lb.is_within_budget(122.0)  # False (> 100 + 20%)
    """

    p99_ms: float
    jitter_tolerance_pct: float = 20.0

    def __post_init__(self) -> None:
        if self.p99_ms <= 0:
            raise InvalidConfigurationError(
                "p99_ms must be positive", context={"p99_ms": self.p99_ms}
            )
        if not (0 <= self.jitter_tolerance_pct <= 100):
            raise InvalidConfigurationError(
                "jitter_tolerance_pct must be in [0, 100]"
            )

    @property
    def hard_ceiling_ms(self) -> float:
        """Absolute maximum including jitter tolerance."""
        return self.p99_ms * (1.0 + self.jitter_tolerance_pct / 100.0)

    def is_within_budget(self, observed_ms: float) -> bool:
        """Return True if *observed_ms* is under the hard ceiling."""
        return observed_ms <= self.hard_ceiling_ms

    @classmethod
    def interactive(cls) -> "LatencyBound":
        """Interactive / chat: 100ms p99."""
        return cls(p99_ms=100.0)

    @classmethod
    def batch(cls) -> "LatencyBound":
        """Batch / background: 10 000ms p99."""
        return cls(p99_ms=10_000.0, jitter_tolerance_pct=50.0)

    @classmethod
    def real_time(cls) -> "LatencyBound":
        """Real-time streaming: 30ms p99, tight jitter."""
        return cls(p99_ms=30.0, jitter_tolerance_pct=5.0)


@dataclass(frozen=True)
class MemoryBound:
    """
    Memory usage ceiling with optional swap policy.

    Parameters
    ----------
    max_bytes : int
        Hard memory limit in bytes.
    allow_swap : bool
        Whether to spill to disk / secondary tier when limit approaches.
    evict_at_pct : float
        Trigger eviction when memory usage reaches this % of max_bytes.

    Example
    -------
    >>> mb = MemoryBound(max_bytes=8 * 1024**3)  # 8 GB
    >>> mb.eviction_threshold_bytes
    6_442_450_944
    """

    max_bytes: int
    allow_swap: bool = False
    evict_at_pct: float = 80.0

    def __post_init__(self) -> None:
        if self.max_bytes <= 0:
            raise InvalidConfigurationError(
                "max_bytes must be positive", context={"max_bytes": self.max_bytes}
            )
        if not (0 < self.evict_at_pct < 100):
            raise InvalidConfigurationError(
                "evict_at_pct must be in (0, 100)",
                context={"evict_at_pct": self.evict_at_pct},
            )

    @property
    def eviction_threshold_bytes(self) -> int:
        """Bytes at which eviction should begin."""
        return int(self.max_bytes * self.evict_at_pct / 100.0)

    @property
    def max_gib(self) -> float:
        """Limit expressed as GiB."""
        return self.max_bytes / (1024**3)

    @classmethod
    def gpu_8gb(cls) -> "MemoryBound":
        return cls(max_bytes=8 * 1024**3, allow_swap=False)

    @classmethod
    def gpu_80gb(cls) -> "MemoryBound":
        return cls(max_bytes=80 * 1024**3, allow_swap=False)

    @classmethod
    def system_32gb(cls) -> "MemoryBound":
        return cls(max_bytes=32 * 1024**3, allow_swap=True, evict_at_pct=70.0)


@dataclass(frozen=True)
class ComputeBudget:
    """
    Composite resource budget combining latency and memory bounds.

    Attributes
    ----------
    latency : LatencyBound
    memory  : MemoryBound
    max_batch_tokens : int
        Hard ceiling on total tokens per request batch.

    Example
    -------
    >>> budget = ComputeBudget.interactive_gpu_8gb()
    >>> budget.fits_tokens(4096)  # True
    """

    latency: LatencyBound
    memory: MemoryBound
    max_batch_tokens: int = 8192

    def __post_init__(self) -> None:
        if self.max_batch_tokens <= 0:
            raise InvalidConfigurationError(
                "max_batch_tokens must be positive"
            )

    def fits_tokens(self, token_count: int) -> bool:
        return token_count <= self.max_batch_tokens

    @classmethod
    def interactive_gpu_8gb(cls) -> "ComputeBudget":
        return cls(
            latency=LatencyBound.interactive(),
            memory=MemoryBound.gpu_8gb(),
            max_batch_tokens=4096,
        )

    @classmethod
    def batch_gpu_80gb(cls) -> "ComputeBudget":
        return cls(
            latency=LatencyBound.batch(),
            memory=MemoryBound.gpu_80gb(),
            max_batch_tokens=131_072,
        )


@dataclass(frozen=True)
class QoSPolicy:
    """
    Quality-of-Service policy governing a client's resource entitlement.

    Attributes
    ----------
    tier                : str   – "free" | "standard" | "enterprise"
    priority            : int   – scheduling priority (higher = first)
    max_concurrent_reqs : int   – per-user concurrency cap
    daily_token_budget  : int   – total tokens per calendar day (0 = unlimited)
    compute_budget      : ComputeBudget
    enable_streaming    : bool  – WebSocket / SSE streaming permitted

    Example
    -------
    >>> policy = QoSPolicy.enterprise()
    >>> policy.allows_streaming
    True
    """

    tier: str
    priority: int
    max_concurrent_reqs: int
    daily_token_budget: int
    compute_budget: ComputeBudget
    enable_streaming: bool = True

    def __post_init__(self) -> None:
        valid_tiers = {"free", "standard", "enterprise", "internal"}
        if self.tier not in valid_tiers:
            raise InvalidConfigurationError(
                f"tier must be one of {valid_tiers}",
                context={"tier": self.tier},
            )
        if self.priority < 0:
            raise InvalidConfigurationError("priority must be >= 0")
        if self.max_concurrent_reqs <= 0:
            raise InvalidConfigurationError("max_concurrent_reqs must be > 0")

    @property
    def allows_streaming(self) -> bool:
        return self.enable_streaming

    @property
    def is_unlimited(self) -> bool:
        return self.daily_token_budget == 0

    @classmethod
    def free(cls) -> "QoSPolicy":
        return cls(
            tier="free",
            priority=0,
            max_concurrent_reqs=2,
            daily_token_budget=50_000,
            compute_budget=ComputeBudget.interactive_gpu_8gb(),
            enable_streaming=False,
        )

    @classmethod
    def standard(cls) -> "QoSPolicy":
        return cls(
            tier="standard",
            priority=1,
            max_concurrent_reqs=10,
            daily_token_budget=500_000,
            compute_budget=ComputeBudget.interactive_gpu_8gb(),
            enable_streaming=True,
        )

    @classmethod
    def enterprise(cls) -> "QoSPolicy":
        return cls(
            tier="enterprise",
            priority=2,
            max_concurrent_reqs=100,
            daily_token_budget=0,  # unlimited
            compute_budget=ComputeBudget.batch_gpu_80gb(),
            enable_streaming=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLING PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SamplingParameters:
    """
    Validated decoding and sampling hyper-parameters.

    All fields validated at construction so downstream code can trust
    the values without additional guards.

    Attributes
    ----------
    temperature         : float – logit scaling (0 = greedy, ∞ = uniform)
    top_k               : int   – 0 = disabled
    top_p               : float – 1.0 = disabled
    min_p               : float – minimum probability relative to top token
    repetition_penalty  : float – 1.0 = disabled (> 1 penalises repeats)
    max_new_tokens      : int   – generation budget
    min_new_tokens      : int   – minimum tokens before EOS is permitted
    do_sample           : bool  – False = greedy argmax
    seed                : int | None – for reproducibility
    stop_token_ids      : frozenset[int] – EOS-equivalents
    presence_penalty    : float – OpenAI-style presence penalty
    frequency_penalty   : float – OpenAI-style frequency penalty
    best_of             : int   – generate N, return highest-probability

    Example
    -------
    >>> params = SamplingParameters.greedy(max_new_tokens=256)
    >>> params.is_greedy
    True

    >>> params = SamplingParameters.creative()
    >>> params.temperature
    1.1
    """

    temperature: float = 1.0
    top_k: int = 0
    top_p: float = 1.0
    min_p: float = 0.0
    repetition_penalty: float = 1.0
    max_new_tokens: int = 512
    min_new_tokens: int = 0
    do_sample: bool = True
    seed: Optional[int] = None
    stop_token_ids: FrozenSet[int] = field(default_factory=frozenset)
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    best_of: int = 1

    def __post_init__(self) -> None:
        if self.temperature < 0:
            raise InvalidConfigurationError(
                "temperature must be >= 0", context={"temperature": self.temperature}
            )
        if self.top_k < 0:
            raise InvalidConfigurationError(
                "top_k must be >= 0", context={"top_k": self.top_k}
            )
        if not (0.0 < self.top_p <= 1.0):
            raise InvalidConfigurationError(
                "top_p must be in (0, 1]", context={"top_p": self.top_p}
            )
        if not (0.0 <= self.min_p < 1.0):
            raise InvalidConfigurationError(
                "min_p must be in [0, 1)", context={"min_p": self.min_p}
            )
        if self.repetition_penalty <= 0:
            raise InvalidConfigurationError(
                "repetition_penalty must be > 0"
            )
        if self.max_new_tokens <= 0:
            raise InvalidConfigurationError("max_new_tokens must be > 0")
        if self.min_new_tokens < 0:
            raise InvalidConfigurationError("min_new_tokens must be >= 0")
        if self.min_new_tokens > self.max_new_tokens:
            raise InvalidConfigurationError(
                "min_new_tokens must be <= max_new_tokens"
            )
        if self.best_of <= 0:
            raise InvalidConfigurationError("best_of must be > 0")
        if not (-2.0 <= self.presence_penalty <= 2.0):
            raise InvalidConfigurationError("presence_penalty must be in [-2, 2]")
        if not (-2.0 <= self.frequency_penalty <= 2.0):
            raise InvalidConfigurationError("frequency_penalty must be in [-2, 2]")

    # ── derived helpers ────────────────────────────────────────────────────

    @property
    def is_greedy(self) -> bool:
        """True when decoding is fully deterministic (temperature == 0 or do_sample == False)."""
        return self.temperature == 0.0 or not self.do_sample

    @property
    def effective_temperature(self) -> float:
        """Clamp temperature to a safe minimum for numerical stability."""
        return max(self.temperature, 1e-7)

    @property
    def uses_top_k(self) -> bool:
        return self.top_k > 0

    @property
    def uses_top_p(self) -> bool:
        return self.top_p < 1.0

    @property
    def uses_min_p(self) -> bool:
        return self.min_p > 0.0

    @property
    def uses_repetition_penalty(self) -> bool:
        return self.repetition_penalty != 1.0

    # ── factories ─────────────────────────────────────────────────────────

    @classmethod
    def greedy(cls, max_new_tokens: int = 512, **kwargs: object) -> "SamplingParameters":
        """Deterministic greedy decoding."""
        return cls(
            temperature=0.0,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            **kwargs,  # type: ignore[arg-type]
        )

    @classmethod
    def balanced(cls, max_new_tokens: int = 512) -> "SamplingParameters":
        """Balanced sampling (GPT-4 defaults)."""
        return cls(
            temperature=0.7,
            top_p=0.9,
            max_new_tokens=max_new_tokens,
            do_sample=True,
        )

    @classmethod
    def creative(cls, max_new_tokens: int = 1024) -> "SamplingParameters":
        """High-diversity creative generation."""
        return cls(
            temperature=1.1,
            top_k=50,
            top_p=0.95,
            repetition_penalty=1.3,
            max_new_tokens=max_new_tokens,
            do_sample=True,
        )

    @classmethod
    def precise(cls, max_new_tokens: int = 256) -> "SamplingParameters":
        """Low-temperature precise generation."""
        return cls(
            temperature=0.2,
            top_p=0.8,
            max_new_tokens=max_new_tokens,
            do_sample=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# TOKENIZER SPEC
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class TokenizerSpec:
    """
    Immutable tokenizer identity and special-token registry.

    Attributes
    ----------
    model_id      : str            – HuggingFace model ID or local path
    vocab_size    : int            – vocabulary cardinality
    bos_token_id  : int | None     – beginning-of-sequence token
    eos_token_id  : int | None     – end-of-sequence token
    pad_token_id  : int | None     – padding token
    unk_token_id  : int | None     – unknown token
    add_special_tokens : bool      – whether to prepend/append BOS/EOS
    max_length    : int            – tokenization truncation limit
    """

    model_id: str
    vocab_size: int
    bos_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    pad_token_id: Optional[int] = None
    unk_token_id: Optional[int] = None
    add_special_tokens: bool = True
    max_length: int = 2048

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise InvalidConfigurationError("model_id must not be blank")
        if self.vocab_size <= 0:
            raise InvalidConfigurationError("vocab_size must be > 0")
        if self.max_length <= 0:
            raise InvalidConfigurationError("max_length must be > 0")

    def token_is_special(self, token_id: int) -> bool:
        """Return True if *token_id* is one of the registered special tokens."""
        special = {
            self.bos_token_id,
            self.eos_token_id,
            self.pad_token_id,
            self.unk_token_id,
        }
        special.discard(None)
        return token_id in special  # type: ignore[operator]

    @classmethod
    def gpt2(cls) -> "TokenizerSpec":
        return cls(
            model_id="gpt2",
            vocab_size=50_257,
            bos_token_id=50_256,
            eos_token_id=50_256,
            pad_token_id=50_256,
            max_length=1024,
        )

    @classmethod
    def llama3(cls) -> "TokenizerSpec":
        return cls(
            model_id="meta-llama/Meta-Llama-3-8B",
            vocab_size=128_256,
            bos_token_id=128_000,
            eos_token_id=128_001,
            pad_token_id=128_001,
            max_length=8192,
        )


__all__ = [
    # Enums
    "AttentionVariant",
    "BackendTag",
    "EvictionPolicy",
    "PrecisionMode",
    # Value Objects
    "BackendCapability",
    "BackendDescriptor",
    "ComputeBudget",
    "LatencyBound",
    "MemoryBound",
    "ModelDimensions",
    "QoSPolicy",
    "SamplingParameters",
    "TensorShape",
    "TokenizerSpec",
]
