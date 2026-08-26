# 💡 Example: Compiler & Kernel Benchmark Suite

This script benchmarks latency and throughput across Eager PyTorch, TorchInductor (`torch.compile`), TensorRT, and Polyglot native kernels.

---

## 🐍 Complete Benchmark Script

```python
import time
import torch
from optimization_core.compiler import compile_model
from optimization_core.polyglot_core.core.attention.engine import PolyglotAttentionEngine

def benchmark_execution(name, fn, warmup=20, iters=100):
    # Warmup
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()

    # Benchmark
    start = time.perf_counter()
    for _ in range(iters):
        fn()
    torch.cuda.synchronize()
    elapsed = (time.perf_counter() - start) / iters * 1000  # ms
    print(f"[{name}] Mean Execution Latency: {elapsed:.3f} ms")
    return elapsed

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch, heads, seq, dim = 16, 16, 1024, 64
    
    q = torch.randn(batch, heads, seq, dim, device=device, dtype=torch.float16)
    k = torch.randn(batch, heads, seq, dim, device=device, dtype=torch.float16)
    v = torch.randn(batch, heads, seq, dim, device=device, dtype=torch.float16)

    # 1. PyTorch SDPA Native
    benchmark_execution("PyTorch Native SDPA", lambda: torch.nn.functional.scaled_dot_product_attention(q, k, v))

    # 2. Polyglot Rust/CUDA Engine
    engine = PolyglotAttentionEngine(backend="rust_cuda_fused")
    benchmark_execution("Polyglot Rust/CUDA Engine", lambda: engine.forward(q, k, v))

if __name__ == "__main__":
    main()
```
