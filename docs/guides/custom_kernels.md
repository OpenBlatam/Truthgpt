# Custom Kernels & Compiler Integration Guide

Learn how to author, compile, benchmark, and register custom **Triton** and **CUDA C++** kernels into the TruthGPT Optimization Core.

---

## ⚡ 1. Writing a Custom Triton Kernel

Triton allows writing high-performance GPU kernels in Python with block-level parallel programming:

```python
import torch
import triton
import triton.language as tl

@triton.jit
def _fused_gelu_kernel(
    x_ptr,
    out_ptr,
    n_elements,
    BLOCK_SIZE: tl.constexpr
):
    # Compute 1D block program ID
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements

    # Load from Global Memory (HBM) into on-chip SRAM registers
    x = tl.load(x_ptr + offsets, mask=mask)

    # Fast GELU approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    sqrt_2_over_pi = 0.7978845608028654
    inner = sqrt_2_over_pi * (x + 0.044715 * x * x * x)
    tanh_out = (tl.exp(2 * inner) - 1) / (tl.exp(2 * inner) + 1)
    gelu = 0.5 * x * (1.0 + tanh_out)

    # Store result back to Global Memory
    tl.store(out_ptr + offsets, gelu, mask=mask)

def custom_fused_gelu(x: torch.Tensor) -> torch.Tensor:
    out = torch.empty_like(x)
    n_elements = x.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
    _fused_gelu_kernel[grid](x, out, n_elements, BLOCK_SIZE=1024)
    return out
```

---

## 🏎️ 2. Benchmarking Kernel Speedup

Use Triton's built-in benchmarking utilities:

```python
@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['N'],
        x_vals=[128 * i for i in range(2, 64)],
        line_arg='provider',
        line_vals=['triton', 'torch'],
        line_names=['Custom Triton Kernel', 'PyTorch Native'],
        styles=[('blue', '-'), ('green', '--')],
        ylabel='Execution Time (ms)',
        plot_name='fused-gelu-performance',
        args={}
    )
)
def benchmark(N, provider):
    x = torch.randn(N, 4096, device='cuda', dtype=torch.float16)
    if provider == 'torch':
        return triton.testing.do_bench(lambda: torch.nn.functional.gelu(x))
    if provider == 'triton':
        return triton.testing.do_bench(lambda: custom_fused_gelu(x))

benchmark.run(save_path='.', show_plots=True)
```

---

## 🔌 3. Registering Kernels in the Compiler Subsystem

Integrate your custom kernel with the dynamic registry:

```python
from registries.unified_registry import KERNEL_REGISTRY

@KERNEL_REGISTRY.register("custom_fused_gelu")
class FusedGELUKernel:
    @staticmethod
    def forward(x: torch.Tensor) -> torch.Tensor:
        return custom_fused_gelu(x)
```

Now enable it in your configuration YAML:
```yaml
compiler:
  custom_kernels:
    activation: "custom_fused_gelu"
```
