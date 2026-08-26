# Custom Triton & CUDA Kernels

TruthGPT Optimization Core provides a high-performance kernel development and dispatch framework (`compiler/kernels/` and `optimizers/triton_optimizations.py`), enabling developers to write, JIT-compile, and benchmark custom GPU kernels written in OpenAI Triton and CUDA C++.

---

## 🛠️ Triton Kernel Architecture

Triton allows writing block-level GPU programs in Python that compile directly to high-efficiency PTX / SASS machine code, achieving performance competitive with hand-tuned CUDA C++ while maintaining readability.

```mermaid
graph LR
    PyTriton["Triton Python Kernel (@triton.jit)"] --> TritonIR["Triton MLIR / LLVM-IR"]
    TritonIR --> Autotuner["Triton Autotuner (Grid / Block Exploration)"]
    Autotuner --> PTX["NVIDIA PTX Code"]
    PTX --> GPU["GPU Hardware Execution"]
```

---

## ⚡ Writing a Custom Fused Kernel Example: Fused RMSNorm

Below is an example of writing and registering a custom Triton fused RMSNorm kernel:

```python
import torch
import triton
import triton.language as tl

@triton.jit
def _rmsnorm_kernel(
    X_ptr,        # Pointer to input tensor
    Y_ptr,        # Pointer to output tensor
    W_ptr,        # Pointer to weights
    stride_row,   # Stride between rows
    N_COLS: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
    EPS: tl.constexpr
):
    row_idx = tl.program_id(0)
    row_start_ptr = X_ptr + row_idx * stride_row
    out_start_ptr = Y_ptr + row_idx * stride_row

    # Load row into registers
    offsets = tl.arange(0, BLOCK_SIZE)
    mask = offsets < N_COLS
    x = tl.load(row_start_ptr + offsets, mask=mask, other=0.0)

    # Compute variance / RMS
    variance = tl.sum(x * x, axis=0) / N_COLS
    rsqrt = 1.0 / tl.sqrt(variance + EPS)

    # Load weight & multiply
    w = tl.load(W_ptr + offsets, mask=mask, other=1.0)
    out = x * rsqrt * w

    # Write back to global memory
    tl.store(out_start_ptr + offsets, out, mask=mask)

def fast_rmsnorm(x: torch.Tensor, weight: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    M, N = x.shape
    y = torch.empty_like(x)
    BLOCK_SIZE = triton.next_power_of_2(N)
    
    # Launch grid
    _rmsnorm_kernel[(M,)](
        x, y, weight,
        x.stride(0),
        N_COLS=N,
        BLOCK_SIZE=BLOCK_SIZE,
        EPS=eps,
        num_warps=4
    )
    return y
```

---

## 🏎️ Kernel Autotuning & Performance Registry

TruthGPT includes a kernel benchmark harness that automatically explores multiple block configurations and selects the optimal kernel grid for the runtime GPU:

```python
@triton.autotune(
    configs=[
        triton.Config({'BLOCK_SIZE': 64, 'num_warps': 2}),
        triton.Config({'BLOCK_SIZE': 128, 'num_warps': 4}),
        triton.Config({'BLOCK_SIZE': 256, 'num_warps': 8}),
        triton.Config({'BLOCK_SIZE': 512, 'num_warps': 8}),
    ],
    key=['N_COLS'],
)
@triton.jit
def autotuned_kernel(...):
    # Kernel implementation
    pass
```
