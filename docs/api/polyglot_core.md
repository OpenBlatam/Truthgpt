# Polyglot Core API Reference

The `polyglot_core` subsystem integrates domain-driven architecture, immutable Value Objects, and foreign function interface (FFI) bindings across **Rust**, **C++**, **Go**, **Julia**, and **Elixir** to achieve bare-metal performance and memory safety.

---

## 🏛️ Polyglot Core Architecture

```
polyglot_core/
├── domain/                    # Domain models, value objects, domain events
│   ├── value_objects.py       # Immutable strongly-typed value objects
│   └── entities.py            # Lifecycle entities & identity tracking
├── infrastructure/            # Hardware abstraction & FFI bridge adapters
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
    BatchSize,
    LearningRate,
    SequenceLength,
    TensorShape,
    MemoryBudget,
    PrecisionMode,
)

# Immutable validated instances
bs = BatchSize(value=32)
lr = LearningRate(value=1e-4)
seq_len = SequenceLength(value=2048)
budget = MemoryBudget(max_gpu_memory_gb=16.0)

# Validation errors are raised immediately if invalid values are passed
# e.g., BatchSize(-1) raises InvalidValueObjectException
```

---

## 🦀 Multi-Language Native FFI Bindings

### 1. Rust Core Engine (`rust_core/`)
- **Role**: Memory-safe ring buffers, token stream chunking, and zero-copy IPC.
- **Python Bridge**: Implemented via `PyO3` / `cffi`.
- **Key Primitives**:
  - `RustRingBuffer`: Lock-free multi-producer single-consumer circular buffer.
  - `FastTokenizerStream`: Multi-threaded token byte-pair encoding without GIL locking.

```python
from polyglot_core.infrastructure.rust_bridge import RustStreamBuffer

buffer = RustStreamBuffer(capacity_bytes=1024 * 1024 * 64)
buffer.push_bytes(raw_token_bytes)
```

---

### 2. C++20 Core Engine (`cpp_core/`)
- **Role**: High-performance SIMD matrix operations (AVX-512) and low-level CUDA stream synchronizations.
- **Key Primitives**:
  - `NativeTensorAlloc`: Paged memory allocator avoiding OS virtual memory page faults.
  - `FastQuantizer`: SIMD-accelerated 8-bit / 4-bit weight scaling.

```python
from polyglot_core.infrastructure.cpp_bridge import CppTensorOps

# Ultra-fast SIMD vector operations
quantized_weights = CppTensorOps.quantize_int8(weight_tensor)
```

---

### 3. Julia Core (`julia_core/`)
- **Role**: Scientific mathematical calculations, high-precision differential equation solving, and hyperparameter loss landscape analysis.

```python
from polyglot_core.infrastructure.julia_bridge import JuliaOptimizer

loss_surface_curvature = JuliaOptimizer.compute_hessian_spectrum(model_weights)
```

---

### 4. Go & Elixir Modules (`go_core/`, `elixir_core/`)
- **Go Core**: High-concurrency network streaming proxies and Prometheus telemetry collection.
- **Elixir Core**: Fault-tolerant Erlang/OTP supervision tree managing multi-node worker health and heartbeat recovery.

---

## 🧪 Polyglot Diagnostics & Benchmarks

Run the polyglot integration verification suite:

```bash
# Execute polyglot core tests
pytest polyglot_core/tests/

# Run multi-language FFI speed benchmark
python polyglot_core/benchmarking/run_polyglot_benchmark.py
```
