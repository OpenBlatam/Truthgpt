# ⚡ Quickstart: Compiler & Hardware Acceleration

The TruthGPT Compiler pipeline provides JIT (Just-In-Time) and AOT (Ahead-Of-Time) compilation, MLIR graph optimizations, TensorRT engine generation, and multi-language polyglot execution backends.

---

## 🚀 1. PyTorch 2.0+ Graph Compilation

Leverage `torch.compile` directly inside your model creation or training pipeline:

```python
import torch
from optimization_core.compiler import compile_model

# 1. Instantiate any PyTorch Transformer
model = torch.nn.Sequential(
    torch.nn.Linear(1024, 4096),
    torch.nn.GELU(),
    torch.nn.Linear(4096, 1024)
).cuda()

# 2. Compile model with hardware-specific optimizations
compiled_model = compile_model(
    model,
    mode="max-autotune",        # 'default', 'reduce-overhead', or 'max-autotune'
    backend="inductor",         # PyTorch Inductor / Triton
    fullgraph=False
)

# 3. Fast execution (kernel fusion & CUDA graphs)
dummy_input = torch.randn(32, 1024, device="cuda")
output = compiled_model(dummy_input)
print("Compiled forward pass successful. Output shape:", output.shape)
```

---

## ⚡ 2. TensorRT Engine Export & Inference

Convert PyTorch Transformer checkpoints into ultra-low-latency NVIDIA TensorRT engines:

```python
from optimization_core.compiler.tensorrt_engines import TensorRTCompiler

# Initialize TRT Compiler targeting FP16 / FP8 precision
compiler = TensorRTCompiler(
    precision="fp16",
    max_batch_size=64,
    max_seq_len=2048,
    workspace_size_gb=4
)

# Build TRT Engine from ONNX or PyTorch model
engine_path = compiler.build_engine(
    model=model,
    sample_input=dummy_input,
    output_path="compiled_models/transformer_fp16.engine"
)
print(f"TensorRT engine serialized to {engine_path}")
```

---

## 🔬 3. Running Polyglot Attention Kernels

TruthGPT includes cross-language native acceleration engines written in Rust, C++, and CUDA:

```python
from optimization_core.polyglot_core.core.attention.engine import PolyglotAttentionEngine

engine = PolyglotAttentionEngine(backend="rust_cuda_fused")

q = torch.randn(8, 12, 512, 64, device="cuda", dtype=torch.float16)
k = torch.randn(8, 12, 512, 64, device="cuda", dtype=torch.float16)
v = torch.randn(8, 12, 512, 64, device="cuda", dtype=torch.float16)

# Execute high-throughput attention computation
context = engine.forward(q, k, v, is_causal=True)
print("Polyglot Attention output shape:", context.shape)
```

---

## 📊 4. Running Compiler Benchmarks

Benchmark execution speed across Eager PyTorch, TorchInductor, TensorRT, and Polyglot engines:

```bash
# Run compiler throughput & latency benchmark suite
python compiler_demo.py --benchmark --batch-size 32 --seq-len 512
```

---

## ⏭️ Next Steps

- Explore [Compiler & Kernel Tuning](../guides/compiler_and_kernels.md).
- Review the [Compiler Architecture](../architecture/compiler_runtime.md).
- Read the [Compiler API Reference](../api/compiler.md).
