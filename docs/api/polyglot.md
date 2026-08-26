# 🌐 Polyglot Core API Reference

The `polyglot_core` package exposes multi-language runtime bindings and unified interfaces for high-performance tensor operations implemented in Rust, C++, Go, Julia, and Elixir.

---

## 🏛️ `PolyglotAttentionEngine`

```python
from optimization_core.polyglot_core.core.attention.engine import PolyglotAttentionEngine
```

### Signature
```python
class PolyglotAttentionEngine:
    def __init__(self, backend: str = "auto"):
        """
        backend options:
          - 'auto': Automatically picks fastest compiled native backend
          - 'rust_cuda_fused': Native Rust-wrapped CUDA kernel
          - 'cpp_tensorrt': C++ TensorRT FlashAttention engine
          - 'torch_sdpa': PyTorch 2.0+ native SDPA fallback
        """
```

### Methods
- **`forward(q, k, v, mask=None, is_causal=True, scale=None) -> torch.Tensor`**:
  Executes attention dot-product without intermediate $O(N^2)$ memory materialization.

---

## 🦀 Rust Core Native Bindings (`rust_core`)

Accessible via Python C-ABI bindings:

```python
import truthgpt_rust_core as rcore

# Zero-copy parallel string tokenization
tokens = rcore.tokenize_batch(text_list, vocab_path="vocab.json", max_len=512)

# Lock-free RingBuffer for high-speed dataloading
buffer = rcore.RingBuffer(capacity=10000)
```

---

## ⚡ C++ Core CUDA Bindings (`cpp_core`)

Accessible via PyBind11:

```python
import truthgpt_cpp_core as ccore

# Fast in-place RMSNorm + Residual addition
ccore.fused_rmsnorm_residual_(tensor_x, residual_tensor, weight_tensor, eps=1e-6)

# Custom quantized matrix multiplication (INT8 / FP8)
out = ccore.quantized_gemm(weight_int8, scales, input_fp16)
```

---

## 🔬 Scientific Simulations (`julia_core`)

Used by PiMoE for Hamiltonian constraint solving and numerical integration:

```python
from optimization_core.julia_core import JuliaPhysicsBridge

bridge = JuliaPhysicsBridge()
hamiltonian_grads = bridge.compute_hamiltonian_gradient(state_tensor)
```
