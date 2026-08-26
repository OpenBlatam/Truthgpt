# Practical Guide: Authoring Custom Triton Kernels

This guide demonstrates how to author, benchmark, and register a custom OpenAI **Triton** GPU kernel within the TruthGPT Compiler Subsystem.

---

## ⚡ 1. Writing the Triton Kernel

Create `compiler/kernels/custom_gelu.py`:

```python
import torch
import triton
import triton.language as tl

@triton.jit
def _fast_gelu_kernel(
    x_ptr,
    y_ptr,
    n_elements,
    BLOCK_SIZE: tl.constexpr
):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    
    x = tl.load(x_ptr + offsets, mask=mask)
    # Fast GELU approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    sqrt_2_over_pi = 0.7978845608
    tanh_in = sqrt_2_over_pi * (x + 0.044715 * x * x * x)
    y = 0.5 * x * (1.0 + tl.math.tanh(tanh_in))
    
    tl.store(y_ptr + offsets, y, mask=mask)

def fast_gelu(x: torch.Tensor) -> torch.Tensor:
    y = torch.empty_like(x)
    n_elements = x.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
    _fast_gelu_kernel[grid](x, y, n_elements, BLOCK_SIZE=1024)
    return y
```

---

## 🛠️ 2. Registering with TruthGPT Factory

```python
from factories.registry import ACTIVATIONS

@ACTIVATIONS.register("fast_gelu")
class FastGELUModule(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return fast_gelu(x)
```

Now you can use `activation: "fast_gelu"` in your YAML configuration files.
