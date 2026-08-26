# Rust & C++ Acceleration Kernels

The **Rust and C++ native engines** provide memory-safe, ultra-low latency compute primitives for TruthGPT.

---

## 🦀 Rust Core (`rust_core/`)

### 1. Parallel BPE Tokenizer
- **Implementation**: Built with Rayon work-stealing parallelism in Rust.
- **Performance**: Up to $12\times$ faster tokenization speed over single-threaded Python implementations.
- **Safety**: Complete memory safety with zero data races.

### 2. Lock-Free Ring Buffers
- Used for high-frequency streaming of training metrics and inference token generation across async tasks without mutex contention.

---

## ⚡ C++ CUDA Core (`cpp_core/`)

### 1. Custom Tensor Kernels
- **Location**: `cpp_core/src/kernels/`
- **Capabilities**:
  - Pinned memory allocation (`cudaHostAlloc`) for asynchronous GPU transfers.
  - Custom CUDA warp-level primitives (`__shfl_xor_sync`) for fast intra-warp reduction.
  - Native half-precision matrix multiplication wrappers.

---

## 🛠️ Building Native Extensions

### Building with Cargo (Rust)

```bash
cd rust_core
cargo build --release
```

### Building with CMake (C++)

```bash
cd cpp_core
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### Building with Bazel (Unified)

```bash
bazel build //...
```
