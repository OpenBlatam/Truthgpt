# 🔬 Compiler Optimization & Custom Kernels Guide

This guide details how to write, compile, autotune, and register custom Triton and CUDA kernels into the TruthGPT compiler pipeline.

---

## 🛠️ 1. Writing Custom Triton Kernels

Triton allows writing block-level fused GPU kernels directly in Python with near-C++/CUDA performance.

### Example: Fused SiLU + Gating (SwiGLU)

```python
import triton
import triton.language as tl
import torch

@triton.jit
def _swiglu_fused_kernel(
    X_ptr, Gate_ptr, Out_ptr,
    n_elements,
    BLOCK_SIZE: tl.constexpr
):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements

    # Load vectors from HBM into SRAM
    x = tl.load(X_ptr + offsets, mask=mask)
    gate = tl.load(Gate_ptr + offsets, mask=mask)

    # Compute SiLU(gate) * x
    silu_gate = gate * tl.sigmoid(gate)
    out = silu_gate * x

    # Store back to global HBM
    tl.store(Out_ptr + offsets, out, mask=mask)
```

---

## 🏎️ 2. Triton Autotuning Configurations

TruthGPT uses automated heuristic exploration to discover the best tile dimensions and warp counts for your target GPU:

```python
@triton.autotune(
    configs=[
        triton.Config({'BLOCK_SIZE': 128}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 256}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 512}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 1024}, num_warps=16),
    ],
    key=['n_elements']
)
@triton.jit
def _autotuned_kernel(...):
    ...
```

---

## 🧩 3. Registering Custom Kernels in the Polyglot Core

Register your kernel so `GenericTrainer` or inference engines can instantiate it via configuration:

```python
from optimization_core.compiler.kernels import register_custom_kernel

@register_custom_kernel("my_fast_swiglu")
def custom_swiglu_wrapper(x: torch.Tensor, gate: torch.Tensor) -> torch.Tensor:
    out = torch.empty_like(x)
    n_elements = x.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
    _swiglu_fused_kernel[grid](x, gate, out, n_elements, BLOCK_SIZE=1024)
    return out
```
