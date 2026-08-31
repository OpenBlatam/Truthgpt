# 🔬 Compiler Optimization & Custom Kernels Guide

This guide details how to write, compile, autotune, and register custom Triton and CUDA kernels into the TruthGPT compiler pipeline.

---

## 🛠️ 1. Writing Custom Triton Kernels

OpenAI Triton allows authoring block-level fused GPU kernels directly in Python with near-C++/CUDA performance without writing raw CUDA C++.

### Example 1: Fused SwiGLU Gating Kernel

```python
import torch
import triton
import triton.language as tl

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

### Example 2: Fast GELU Approximation Kernel

```python
@triton.jit
def _fast_gelu_kernel(
    x_ptr, y_ptr, n_elements,
    BLOCK_SIZE: tl.constexpr
):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    
    x = tl.load(x_ptr + offsets, mask=mask)
    # Fast GELU approximation
    sqrt_2_over_pi = 0.7978845608
    tanh_in = sqrt_2_over_pi * (x + 0.044715 * x * x * x)
    y = 0.5 * x * (1.0 + tl.math.tanh(tanh_in))
    
    tl.store(y_ptr + offsets, y, mask=mask)
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

## 🧩 3. Registering Custom Kernels in the Factory Registry

Register your kernel so `GenericTrainer` or inference engines can instantiate it dynamically via YAML configuration:

```python
from factories.registry import ACTIVATIONS

def fast_gelu(x: torch.Tensor) -> torch.Tensor:
    y = torch.empty_like(x)
    n_elements = x.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
    _fast_gelu_kernel[grid](x, y, n_elements, BLOCK_SIZE=1024)
    return y

@ACTIVATIONS.register("fast_gelu")
class FastGELUModule(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return fast_gelu(x)
```

Now you can specify `activation: "fast_gelu"` in your YAML configuration.
