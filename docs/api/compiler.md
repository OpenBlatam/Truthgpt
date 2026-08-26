# ⚡ Compiler & Hardware Acceleration API Reference

The `compiler` module provides model compilation, graph optimization passes, MLIR dialect lowers, custom CUDA/Triton kernels, and TensorRT inference engine generation.

---

## 🏛️ `compile_model`

```python
from optimization_core.compiler import compile_model
```

### Signature
```python
def compile_model(
    model: torch.nn.Module,
    mode: str = "default",
    backend: str = "inductor",
    fullgraph: bool = False,
    dynamic: bool = True,
    options: Optional[Dict[str, Any]] = None
) -> torch.nn.Module
```

### Arguments
- **`mode`**: Compilation optimization profile:
  - `"default"`: Balanced compilation latency and step throughput.
  - `"reduce-overhead"`: Integrates CUDA Graphs to eliminate CPU kernel launch bottlenecks (ideal for small batch sizes).
  - `"max-autotune"`: Explores Triton kernel configurations and GEMM tile sizes for maximum runtime speed.
- **`backend`**: Backend compiler (`"inductor"`, `"cudagraphs"`, `"tensorrt"`, `"xla"`).
- **`dynamic`**: Enable dynamic tensor shape handling to prevent recompilations on variable sequence lengths.

---

## 🏎️ `TensorRTCompiler`

```python
from optimization_core.compiler.tensorrt_engines import TensorRTCompiler
```

### Methods
- **`build_engine(model, sample_input, output_path, precision='fp16')`**: Compiles and serializes an NVIDIA TensorRT runtime engine (`.engine`).
- **`load_engine(engine_path)`**: Loads a compiled TensorRT plan and binds GPU memory I/O buffers.
- **`infer(engine, inputs_dict)`**: Executes asynchronous high-throughput inference on CUDA streams.

---

## 🔬 `MLIROptimizer`

```python
from optimization_core.compiler.mlir import MLIROptimizer

optimizer = MLIROptimizer()
mlir_module = optimizer.parse_pytorch_module(model)
optimized_mlir = optimizer.apply_passes(
    mlir_module,
    passes=["fuse-attention", "eliminate-dead-code", "bufferize-in-place"]
)
```

---

## 🎛️ Custom Triton Kernels (`compiler.kernels`)

| Kernel Function | Signature | Description |
| :--- | :--- | :--- |
| **`fused_rotary_attention`** | `(q, k, v, cos, sin, is_causal=True)` | Applies Rotary Positional Embeddings and FlashAttention in a single fused GPU kernel. |
| **`fused_swiglu`** | `(x, gate_weight, up_weight)` | Fused SiLU activation and elementwise Hadamard gate multiplication. |
| **`fused_rmsnorm`** | `(x, weight, eps=1e-6)` | Computes RMSNorm with single-pass variance reduction and residual accumulation. |
