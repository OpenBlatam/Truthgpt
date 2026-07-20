"""
polyglot_core.domain.models
============================
Immutable value objects and entity definitions for the polyglot_core domain.

Design principles
-----------------
* All *value objects* are frozen dataclasses — equality by value, hashable.
* All *entities* carry an opaque ``uid`` field — equality by identity.
* No circular imports: this module imports only stdlib.
* Every public type carries a complete docstring with usage examples.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import FrozenSet, Optional, Sequence, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ModelArchitecture(str, Enum):
    """
    Canonical transformer architecture identifiers.

    Used to select architecture-specific optimisations throughout the stack.

    Example::

        arch = ModelArchitecture.LLAMA
        if arch.is_decoder_only:
            ...
    """
    GPT2          = "gpt2"
    LLAMA         = "llama"
    MISTRAL       = "mistral"
    FALCON        = "falcon"
    MPT           = "mpt"
    BLOOM         = "bloom"
    OPT           = "opt"
    PHI           = "phi"
    GEMMA         = "gemma"
    QWEN          = "qwen"
    INTERNLM      = "internlm"
    CUSTOM        = "custom"

    @property
    def is_decoder_only(self) -> bool:
        """Returns True for autoregressive (decoder-only) architectures."""
        _decoder_only = {
            ModelArchitecture.GPT2, ModelArchitecture.LLAMA,
            ModelArchitecture.MISTRAL, ModelArchitecture.FALCON,
            ModelArchitecture.MPT, ModelArchitecture.BLOOM,
            ModelArchitecture.OPT, ModelArchitecture.PHI,
            ModelArchitecture.GEMMA, ModelArchitecture.QWEN,
            ModelArchitecture.INTERNLM,
        }
        return self in _decoder_only


class PrecisionLevel(str, Enum):
    """
    Floating-point / integer precision levels.

    Ordered by memory footprint (ascending)::

        FP32 > BF16 = FP16 > INT8 > INT4 > FP8
    """
    FP32   = "fp32"
    BF16   = "bf16"
    FP16   = "fp16"
    FP8    = "fp8"
    INT8   = "int8"
    INT4   = "int4"
    INT2   = "int2"

    @property
    def bits(self) -> int:
        """Number of bits per element."""
        _bits_map = {
            PrecisionLevel.FP32: 32,
            PrecisionLevel.BF16: 16,
            PrecisionLevel.FP16: 16,
            PrecisionLevel.FP8: 8,
            PrecisionLevel.INT8: 8,
            PrecisionLevel.INT4: 4,
            PrecisionLevel.INT2: 2,
        }
        return _bits_map[self]

    @property
    def bytes_per_element(self) -> float:
        """Bytes required per scalar element (may be fractional for sub-byte)."""
        return self.bits / 8.0

    def memory_factor_vs(self, other: "PrecisionLevel") -> float:
        """
        Memory ratio of *self* relative to *other*.

        Example::

            ratio = PrecisionLevel.INT8.memory_factor_vs(PrecisionLevel.FP32)
            # → 0.25  (4x smaller)
        """
        return self.bytes_per_element / other.bytes_per_element


class BackendKind(str, Enum):
    """
    Execution backend identifiers.

    Priority order for most workloads: CPP_CUDA > CPP_CPU > RUST > GO > PYTHON.
    """
    PYTHON    = "python"      # Pure-Python fallback — always available
    RUST      = "rust"        # Rust via PyO3 — fast CPU, low memory
    CPP_CPU   = "cpp_cpu"     # C++/Eigen via PyBind11 — SIMD vectorised
    CPP_CUDA  = "cpp_cuda"    # C++/CUDA via PyBind11 — GPU accelerated
    GO        = "go"          # Go services over gRPC — distributed

    @property
    def is_accelerated(self) -> bool:
        """True for hardware-accelerated backends (GPU)."""
        return self == BackendKind.CPP_CUDA

    @property
    def is_native(self) -> bool:
        """True for compiled native backends (Rust / C++)."""
        return self in {BackendKind.RUST, BackendKind.CPP_CPU, BackendKind.CPP_CUDA}

    @property
    def performance_rank(self) -> int:
        """
        Relative performance rank (lower = faster).
        Used for automatic backend selection ordering.
        """
        _rank = {
            BackendKind.CPP_CUDA: 0,
            BackendKind.CPP_CPU:  1,
            BackendKind.RUST:     2,
            BackendKind.GO:       3,
            BackendKind.PYTHON:   4,
        }
        return _rank[self]


class EvictionPolicy(str, Enum):
    """Cache eviction policies."""
    LRU      = "lru"       # Least-Recently-Used  — O(1) via OrderedDict
    LFU      = "lfu"       # Least-Frequently-Used
    FIFO     = "fifo"      # First-In-First-Out
    S3FIFO   = "s3fifo"    # Segmented-3-FIFO (high hit-rate)
    ARC      = "arc"       # Adaptive-Replacement-Cache
    ADAPTIVE = "adaptive"  # Dynamic hybrid (runtime-tuned)


class AttentionPattern(str, Enum):
    """Attention sparsity patterns."""
    FULL      = "full"      # O(N²) — standard dense attention
    CAUSAL    = "causal"    # Causal (autoregressive) mask
    SLIDING   = "sliding"   # Local sliding window
    SPARSE    = "sparse"    # Sparse pattern (BigBird / Longformer)
    FLASH     = "flash"     # Flash-Attention tiled kernel
    LINEAR    = "linear"    # Linear attention approximation


class GenerationStrategy(str, Enum):
    """Token generation decoding strategies."""
    GREEDY      = "greedy"
    SAMPLING    = "sampling"
    BEAM_SEARCH = "beam_search"
    DIVERSE     = "diverse_beam"
    CONTRASTIVE = "contrastive"


class HealthStatus(str, Enum):
    """Coarse-grained component / system health states."""
    HEALTHY   = "healthy"
    DEGRADED  = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN   = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# VALUE OBJECTS  (frozen dataclasses — equality by value)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class TokenSequence:
    """
    Immutable token sequence value object.

    Wraps a tuple of integer token IDs.  Carries optional text for debugging.

    Example::

        seq = TokenSequence.from_list([1, 2, 3], text="hello world")
        print(len(seq))       # 3
        print(seq.token_ids)  # (1, 2, 3)
        extended = seq.append(4)
        print(len(extended))  # 4
    """
    token_ids: Tuple[int, ...]
    text: Optional[str] = None

    @classmethod
    def from_list(
        cls,
        token_ids: Sequence[int],
        text: Optional[str] = None,
    ) -> "TokenSequence":
        """Construct from any sequence of ints."""
        return cls(token_ids=tuple(token_ids), text=text)

    @classmethod
    def empty(cls) -> "TokenSequence":
        """Return an empty token sequence."""
        return cls(token_ids=())

    def append(self, token_id: int) -> "TokenSequence":
        """Return a new sequence with *token_id* appended (immutable)."""
        return TokenSequence(token_ids=self.token_ids + (token_id,), text=self.text)

    def extend(self, token_ids: Sequence[int]) -> "TokenSequence":
        """Return a new sequence with *token_ids* appended (immutable)."""
        return TokenSequence(
            token_ids=self.token_ids + tuple(token_ids),
            text=self.text,
        )

    def __len__(self) -> int:
        return len(self.token_ids)

    def __iter__(self):
        return iter(self.token_ids)

    def __getitem__(self, idx):
        return self.token_ids[idx]


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    """
    Immutable descriptor for a model configuration.

    Used throughout the domain to identify *which* model is being served,
    without coupling to a specific deep-learning framework.

    Example::

        desc = ModelDescriptor(
            name="llama-3-8b",
            architecture=ModelArchitecture.LLAMA,
            precision=PrecisionLevel.BF16,
            vocab_size=32_000,
            d_model=4096,
            n_layers=32,
            n_heads=32,
            n_kv_heads=8,
            max_seq_len=8192,
        )
    """
    name: str
    architecture: ModelArchitecture
    precision: PrecisionLevel
    vocab_size: int
    d_model: int
    n_layers: int
    n_heads: int
    max_seq_len: int
    n_kv_heads: Optional[int] = None          # None → same as n_heads (MHA)
    head_dim: Optional[int] = None            # None → d_model // n_heads
    intermediate_size: Optional[int] = None  # FFN hidden dimension
    rope_theta: float = 10_000.0             # RoPE base theta

    def __post_init__(self) -> None:
        if self.n_kv_heads is None:
            # Bypass frozen restriction via object.__setattr__
            object.__setattr__(self, "n_kv_heads", self.n_heads)
        if self.head_dim is None:
            object.__setattr__(self, "head_dim", self.d_model // self.n_heads)

    @property
    def is_gqa(self) -> bool:
        """True when using Grouped-Query Attention (n_kv_heads < n_heads)."""
        return self.n_kv_heads < self.n_heads  # type: ignore[operator]

    @property
    def kv_cache_bytes_per_token(self) -> int:
        """
        Approximate KV-cache memory in bytes per token per layer.
        Formula: 2 (K + V) × n_kv_heads × head_dim × bytes_per_element
        """
        bpe = self.precision.bytes_per_element
        return int(2 * self.n_kv_heads * self.head_dim * bpe)  # type: ignore

    @property
    def total_kv_cache_bytes(self) -> int:
        """Total KV-cache bytes for full context across all layers."""
        return self.kv_cache_bytes_per_token * self.max_seq_len * self.n_layers


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """
    Immutable record of what a backend can do.

    Populated during backend detection and used by *BackendSelectionService*.

    Example::

        caps = BackendCapabilities(
            kind=BackendKind.CPP_CUDA,
            available=True,
            version="1.2.0",
            features=frozenset({"flash_attention", "kv_cache", "cuda", "int8"}),
            performance_multiplier=100.0,
        )
    """
    kind: BackendKind
    available: bool
    version: str = ""
    features: FrozenSet[str] = field(default_factory=frozenset)
    performance_multiplier: float = 1.0
    error: Optional[str] = None

    def supports(self, feature: str) -> bool:
        """Return True if this backend advertises *feature*."""
        return feature in self.features

    def __str__(self) -> str:
        status = "✓" if self.available else "✗"
        perf = f"{self.performance_multiplier:.0f}x" if self.available else "N/A"
        return f"{status} {self.kind.value} v{self.version} [{perf}]"


@dataclass(frozen=True, slots=True)
class GenerationParameters:
    """
    Immutable generation hyper-parameters (value object).

    Validates all fields at construction time.

    Example::

        params = GenerationParameters(
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.1,
            strategy=GenerationStrategy.SAMPLING,
        )
    """
    max_new_tokens: int = 256
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 0
    repetition_penalty: float = 1.0
    num_beams: int = 1
    eos_token_id: Optional[int] = None
    pad_token_id: Optional[int] = None
    strategy: GenerationStrategy = GenerationStrategy.GREEDY
    seed: int = 42

    def __post_init__(self) -> None:
        if self.max_new_tokens <= 0:
            raise ValueError(f"max_new_tokens must be positive, got {self.max_new_tokens}")
        if not (0.0 < self.temperature <= 100.0):
            raise ValueError(f"temperature must be in (0, 100], got {self.temperature}")
        if not (0.0 < self.top_p <= 1.0):
            raise ValueError(f"top_p must be in (0, 1], got {self.top_p}")
        if self.top_k < 0:
            raise ValueError(f"top_k must be ≥ 0, got {self.top_k}")
        if self.repetition_penalty < 1.0:
            raise ValueError(
                f"repetition_penalty must be ≥ 1.0, got {self.repetition_penalty}"
            )
        if self.num_beams < 1:
            raise ValueError(f"num_beams must be ≥ 1, got {self.num_beams}")

    @classmethod
    def greedy(cls, max_new_tokens: int = 256, **kwargs) -> "GenerationParameters":
        """Convenience constructor for greedy decoding."""
        return cls(
            max_new_tokens=max_new_tokens,
            strategy=GenerationStrategy.GREEDY,
            **kwargs,
        )

    @classmethod
    def sampling(
        cls,
        temperature: float = 0.8,
        top_p: float = 0.9,
        top_k: int = 50,
        max_new_tokens: int = 256,
        **kwargs,
    ) -> "GenerationParameters":
        """Convenience constructor for temperature sampling."""
        return cls(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            strategy=GenerationStrategy.SAMPLING,
            **kwargs,
        )

    @classmethod
    def beam_search(
        cls,
        num_beams: int = 4,
        max_new_tokens: int = 256,
        **kwargs,
    ) -> "GenerationParameters":
        """Convenience constructor for beam-search decoding."""
        return cls(
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
            strategy=GenerationStrategy.BEAM_SEARCH,
            **kwargs,
        )


@dataclass(frozen=True, slots=True)
class CacheKey:
    """
    Canonical KV-cache lookup key.

    Composed of (layer_index, position, namespace) → hashable, value-comparable.

    Example::

        key = CacheKey(layer_index=0, position=42, namespace="session-abc")
        d = {key: tensor}
    """
    layer_index: int
    position: int
    namespace: str = ""

    def __post_init__(self) -> None:
        if self.layer_index < 0:
            raise ValueError(f"layer_index must be ≥ 0, got {self.layer_index}")
        if self.position < 0:
            raise ValueError(f"position must be ≥ 0, got {self.position}")


@dataclass(frozen=True, slots=True)
class AttentionShape:
    """
    Describes the tensor dimensions of an attention layer.

    Example::

        shape = AttentionShape(
            batch_size=4, seq_len=512,
            d_model=4096, n_heads=32, n_kv_heads=8,
        )
        print(shape.head_dim)   # 128
        print(shape.is_gqa)     # True
    """
    batch_size: int
    seq_len: int
    d_model: int
    n_heads: int
    n_kv_heads: int

    @property
    def head_dim(self) -> int:
        """Dimension per attention head."""
        return self.d_model // self.n_heads

    @property
    def is_gqa(self) -> bool:
        """True when using Grouped-Query Attention."""
        return self.n_kv_heads < self.n_heads

    @property
    def query_shape(self) -> Tuple[int, ...]:
        """Expected shape of the Q tensor: (batch, seq, n_heads, head_dim)."""
        return (self.batch_size, self.seq_len, self.n_heads, self.head_dim)

    @property
    def kv_shape(self) -> Tuple[int, ...]:
        """Expected shape of K/V tensors: (batch, seq, n_kv_heads, head_dim)."""
        return (self.batch_size, self.seq_len, self.n_kv_heads, self.head_dim)


# ─────────────────────────────────────────────────────────────────────────────
# ENTITIES  (mutable, equality by UID)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(eq=False)
class GenerationSession:
    """
    Mutable entity representing an in-flight generation session.

    Equality is by *session_id* (identity semantics).

    Lifecycle:
        1. Created via ``GenerationSession.start(...)``
        2. Tokens appended with ``append_token(...)``
        3. Finished via ``finish(reason)``

    Example::

        session = GenerationSession.start(
            prompt=TokenSequence.from_list([1, 2, 3]),
            params=GenerationParameters.sampling(),
        )
        session.append_token(42)
        session.finish("eos")
    """
    session_id: str
    prompt: TokenSequence
    params: GenerationParameters
    generated_tokens: list = field(default_factory=list)
    finish_reason: Optional[str] = None
    _started_at: float = field(default_factory=lambda: __import__("time").perf_counter())

    @classmethod
    def start(
        cls,
        prompt: TokenSequence,
        params: GenerationParameters,
    ) -> "GenerationSession":
        """Create and begin a new generation session."""
        return cls(
            session_id=str(uuid.uuid4()),
            prompt=prompt,
            params=params,
        )

    def append_token(self, token_id: int) -> None:
        """Append a newly generated token to this session."""
        if self.is_finished:
            raise RuntimeError("Cannot append to a finished GenerationSession")
        self.generated_tokens.append(token_id)

    def finish(self, reason: str) -> None:
        """Mark session as complete."""
        self.finish_reason = reason

    @property
    def is_finished(self) -> bool:
        """True once a finish reason has been set."""
        return self.finish_reason is not None

    @property
    def full_sequence(self) -> TokenSequence:
        """Prompt + generated tokens as a single sequence."""
        return self.prompt.extend(self.generated_tokens)

    @property
    def tokens_generated(self) -> int:
        """Number of tokens generated so far."""
        return len(self.generated_tokens)

    @property
    def elapsed_ms(self) -> float:
        """Wall-clock milliseconds elapsed since session started."""
        return (__import__("time").perf_counter() - self._started_at) * 1_000

    @property
    def tokens_per_second(self) -> float:
        """Throughput in tokens/s (0.0 if no tokens yet)."""
        elapsed_s = self.elapsed_ms / 1_000
        if elapsed_s == 0 or self.tokens_generated == 0:
            return 0.0
        return self.tokens_generated / elapsed_s

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GenerationSession):
            return NotImplemented
        return self.session_id == other.session_id

    def __hash__(self) -> int:
        return hash(self.session_id)

    def __repr__(self) -> str:
        return (
            f"GenerationSession(id={self.session_id[:8]}…, "
            f"tokens={self.tokens_generated}, "
            f"finished={self.is_finished})"
        )
