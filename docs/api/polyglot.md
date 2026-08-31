# 🌐 Polyglot Core API Reference

The `polyglot_core` subsystem integrates domain-driven architecture, immutable Value Objects, multi-backend scaled dot-product attention, and foreign function interface (FFI) bridges across **Rust**, **C++**, **Go**, **Julia**, and **Elixir** to achieve bare-metal performance and memory safety.

---

## 🏛️ Polyglot Core Architecture

```
polyglot_core/
├── domain/                    # Domain models, value objects, domain events & exceptions
│   ├── value_objects.py       # Immutable strongly-typed value objects (TensorShape, BackendTag)
│   ├── entities.py            # Lifecycle entities & identity tracking
│   └── exceptions.py          # Domain error hierarchy
├── core/                      # Core computational primitives & multi-backend attention
│   ├── attention/engine.py    # FlashAttention, GQA, SparseAttention, CrossAttention
│   ├── backend.py             # Multi-language backend registry & fallback dispatcher
│   └── cache/                 # KV-cache management & block allocators
├── infrastructure/            # Hardware abstraction & native bridge adapters
├── processing/                # High-throughput batch & stream processors
├── management/                # Resource management & cluster orchestration
└── monitoring/                # Multi-language telemetry & health metrics
```

---

## 📦 Domain & Value Objects API

**Location**: `polyglot_core.domain.value_objects`

Provides immutable, self-validating data structures enforcing system invariants:

```python
from polyglot_core.domain.value_objects import (
    TensorShape,
    ModelDimensions,
    ComputeBudget,
    LatencyBound,
    MemoryBound,
    BackendTag,
    SamplingParameters
)

# 1. Immutable validated tensor shape
shape = TensorShape(dimensions=(4, 32, 512, 128))

# 2. Model dimensions specification
model_dim = ModelDimensions(
    d_model=4096,
    num_heads=32,
    num_kv_heads=8,
    head_dim=128,
    vocab_size=32000
)

# 3. Compute budget & SLA bounds
budget = ComputeBudget(max_latency_ms=50.0, max_memory_mb=8192)
```

---

## 🏛️ Multi-Backend Attention (`polyglot_core.core.attention.engine`)

```python
from polyglot_core.core.attention.engine import (
    Attention,
    FlashAttention,
    GroupedQueryAttention,
    SparseAttention,
    CrossAttention,
    AttentionConfig
)

# Initialize multi-backend FlashAttention
attention = FlashAttention(d_model=4096, n_heads=32)

# Execute forward pass with automatic backend dispatch
result = attention.forward(q, k, v, mask=None, is_causal=True)
print(f"Computed in {result.compute_time_ms:.2f}ms using {result.backend_used}")
```

### Supported Attention Variants:
- **`FlashAttention`**: $O(N)$ memory tiled SRAM computation.
- **`GroupedQueryAttention` (GQA)**: KV-head sharing for high throughput (LLaMA-3/Mistral).
- **`SparseAttention`**: $O(N \times w)$ complexity local sliding window attention.
- **`CrossAttention`**: Multi-modal encoder-decoder cross-attention.

---

## 🦀 Multi-Language Native FFI Engines

| Backend | Language | Directory | Target Responsibilities |
| :--- | :--- | :--- | :--- |
| **Rust** | Rust 2021 | `rust_core/` | Zero-copy lock-free ring buffers, SIMD tokenization, memory-safe IPC |
| **C++** | C++20 | `cpp_core/` | CUDA stream synchronization, AVX-512 vector math, TensorRT bindings |
| **Julia** | Julia 1.10 | `julia_core/` | Differentiable ODE solvers, scientific numerical optimization |
| **Elixir** | Elixir/OTP | `elixir_core/` | Massive concurrent agent actor scheduling and fault-tolerance supervisor trees |
| **Go** | Go 1.22 | `go_core/` | High-concurrency gRPC proxying and distributed cluster coordination |
