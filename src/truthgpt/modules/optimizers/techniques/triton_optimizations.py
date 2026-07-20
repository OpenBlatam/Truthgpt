"""
Triton-optimized kernels for TruthGPT variants.

References:
- Tillet, Kung, Cox (2019) "Triton: An Intermediate Language and Compiler
  for Tiled Neural Network Computations".
- Hsu et al. (2024) "Liger Kernel: Efficient Triton Kernels for LLM Training".
- Su et al. (2021) "RoFormer: Enhanced Transformer with Rotary Position
  Embedding".

This module provides:
  * `TritonLayerNorm` — autograd Function with a NUMERICALLY CORRECT backward
    pass (the prior implementation returned `dy` unchanged, silently
    corrupting gradients during training).
  * `TritonLayerNormModule` — drop-in replacement for `nn.LayerNorm`.
  * `rotary_embed` — RoPE rotation compatible with the standard
    half-split convention used in LLaMA / GPT-NeoX.
  * `block_copy` — KV-cache style block copy helper.

All public functions degrade gracefully to vectorized PyTorch when CUDA or
Triton is unavailable, so the module is safe to import on CPU-only hosts.
"""

import math
import warnings
from typing import Optional, Tuple

import torch

try:
    import triton
    import triton.language as tl
    TRITON_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    warnings.warn("Triton not available. Triton optimizations will fall back to PyTorch.")
    TRITON_AVAILABLE = False
    triton = None  # type: ignore[assignment]
    tl = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Triton kernels (compiled lazily; guarded by TRITON_AVAILABLE).
# ---------------------------------------------------------------------------
if TRITON_AVAILABLE:

    @triton.jit
    def _layer_norm_fwd_kernel(
        X, Y, W, B, Mean, Rstd,
        stride, N, eps,
        BLOCK_SIZE: tl.constexpr,
    ):
        row = tl.program_id(0)
        X += row * stride
        Y += row * stride
        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < N
        x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
        mean = tl.sum(x, axis=0) / N
        x_centered = tl.where(mask, x - mean, 0.0)
        var = tl.sum(x_centered * x_centered, axis=0) / N
        rstd = 1.0 / tl.sqrt(var + eps)
        tl.store(Mean + row, mean)
        tl.store(Rstd + row, rstd)
        w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
        b = tl.load(B + cols, mask=mask, other=0.0).to(tl.float32)
        y = x_centered * rstd * w + b
        tl.store(Y + cols, y, mask=mask)

    @triton.jit
    def _layer_norm_bwd_dx_kernel(
        DY, DX, X, W, Mean, Rstd,
        stride, N,
        BLOCK_SIZE: tl.constexpr,
    ):
        row = tl.program_id(0)
        X += row * stride
        DY += row * stride
        DX += row * stride
        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < N
        x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
        dy = tl.load(DY + cols, mask=mask, other=0.0).to(tl.float32)
        w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
        mean = tl.load(Mean + row)
        rstd = tl.load(Rstd + row)
        x_hat = (x - mean) * rstd
        wdy = w * dy
        c1 = tl.sum(x_hat * wdy, axis=0) / N
        c2 = tl.sum(wdy, axis=0) / N
        dx = (wdy - (x_hat * c1 + c2)) * rstd
        tl.store(DX + cols, dx, mask=mask)


class TritonLayerNorm(torch.autograd.Function):
    """Fused LayerNorm with correct backward."""

    @staticmethod
    def forward(ctx, x: torch.Tensor, gamma: torch.Tensor, beta: torch.Tensor, eps: float) -> torch.Tensor:
        # Always compute via PyTorch reference for numerical parity; on CUDA+Triton
        # we use the fused kernel and cache (mean,rstd) for backward.
        original_dtype = x.dtype
        if not (TRITON_AVAILABLE and x.is_cuda):
            y = torch.nn.functional.layer_norm(x, x.shape[-1:], gamma, beta, eps)
            ctx.save_for_backward(x, gamma, beta)
            ctx.eps = eps
            ctx.used_triton = False
            return y
        x2 = x.contiguous().view(-1, x.shape[-1])
        M, N = x2.shape
        y2 = torch.empty_like(x2)
        mean = torch.empty((M,), dtype=torch.float32, device=x.device)
        rstd = torch.empty((M,), dtype=torch.float32, device=x.device)
        BLOCK_SIZE = triton.next_power_of_2(N)
        num_warps = min(max(BLOCK_SIZE // 256, 1), 8)
        _layer_norm_fwd_kernel[(M,)](
            x2, y2, gamma, beta, mean, rstd,
            x2.stride(0), N, eps,
            BLOCK_SIZE=BLOCK_SIZE, num_warps=num_warps,
        )
        ctx.save_for_backward(x2, gamma, beta, mean, rstd)
        ctx.eps = eps
        ctx.original_shape = x.shape
        ctx.original_dtype = original_dtype
        ctx.used_triton = True
        return y2.view(x.shape).to(original_dtype)

    @staticmethod
    def backward(ctx, dy: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, None]:
        if not getattr(ctx, "used_triton", False):
            x, gamma, beta = ctx.saved_tensors
            eps = ctx.eps
            # Reference autograd backward via re-computation.
            x_req = x.detach().requires_grad_(True)
            g_req = gamma.detach().requires_grad_(True)
            b_req = beta.detach().requires_grad_(True)
            y = torch.nn.functional.layer_norm(x_req, x.shape[-1:], g_req, b_req, eps)
            grads = torch.autograd.grad(y, (x_req, g_req, b_req), grad_outputs=dy)
            return grads[0], grads[1], grads[2], None
        x2, gamma, beta, mean, rstd = ctx.saved_tensors
        dy2 = dy.contiguous().view(-1, x2.shape[-1])
        M, N = x2.shape
        dx2 = torch.empty_like(x2)
        BLOCK_SIZE = triton.next_power_of_2(N)
        num_warps = min(max(BLOCK_SIZE // 256, 1), 8)
        _layer_norm_bwd_dx_kernel[(M,)](
            dy2, dx2, x2, gamma, mean, rstd,
            x2.stride(0), N,
            BLOCK_SIZE=BLOCK_SIZE, num_warps=num_warps,
        )
        x_hat = (x2 - mean.unsqueeze(1)) * rstd.unsqueeze(1)
        dgamma = (dy2 * x_hat).sum(dim=0).to(gamma.dtype)
        dbeta = dy2.sum(dim=0).to(beta.dtype)
        dx = dx2.view(ctx.original_shape).to(ctx.original_dtype)
        return dx, dgamma, dbeta, None


class TritonLayerNormModule(torch.nn.Module):
    """Drop-in replacement for `nn.LayerNorm` backed by `TritonLayerNorm`."""

    def __init__(self, normalized_shape: int, eps: float = 1e-5):
        super().__init__()
        if not isinstance(normalized_shape, int):
            normalized_shape = int(normalized_shape)
        self.normalized_shape = normalized_shape
        self.eps = eps
        self.gamma = torch.nn.Parameter(torch.ones(normalized_shape))
        self.beta = torch.nn.Parameter(torch.zeros(normalized_shape))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        try:
            return TritonLayerNorm.apply(x, self.gamma, self.beta, self.eps)
        except Exception as e:  # pragma: no cover - defensive fallback
            warnings.warn(f"Triton kernel failed ({e}); falling back to PyTorch LayerNorm.")
            return torch.nn.functional.layer_norm(
                x, (self.normalized_shape,), self.gamma, self.beta, self.eps
            )


class TritonOptimizations:
    """Utility class for applying Triton optimizations."""

    @staticmethod
    def replace_layer_norm_with_triton(model: torch.nn.Module) -> torch.nn.Module:
        """Replace every `nn.LayerNorm` in `model` with `TritonLayerNormModule`."""
        for name, module in list(model.named_modules()):
            if isinstance(module, torch.nn.LayerNorm):
                parent_name = ".".join(name.split(".")[:-1])
                parent = model.get_submodule(parent_name) if parent_name else model
                child_name = name.split(".")[-1]
                shape = module.normalized_shape
                if isinstance(shape, (tuple, list)):
                    shape = shape[0]
                triton_norm = TritonLayerNormModule(normalized_shape=shape, eps=module.eps)
                if module.elementwise_affine and module.weight is not None:
                    triton_norm.gamma.data.copy_(module.weight.data)
                    if module.bias is not None:
                        triton_norm.beta.data.copy_(module.bias.data)
                setattr(parent, child_name, triton_norm)
        return model

    @staticmethod
    def is_triton_available() -> bool:
        """True iff Triton is importable AND a CUDA device is visible."""
        return TRITON_AVAILABLE and torch.cuda.is_available()


def rotary_embed(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Apply rotary position embedding (RoPE) to `x`.

    Implements the half-split convention used by LLaMA / GPT-NeoX:
        x = [x1, x2]  ->  [x1*cos - x2*sin, x1*sin + x2*cos].

    `cos` and `sin` must broadcast against the last dim halves of `x`.
    """
    d = x.shape[-1]
    if d % 2 != 0:
        raise ValueError(f"rotary_embed requires an even last dim, got {d}")
    x1, x2 = x[..., : d // 2], x[..., d // 2 :]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


def block_copy(dst: torch.Tensor, src: torch.Tensor, dst_offset: int) -> None:
    """Copy `src` tokens into `dst` starting at `dst_offset` on the time axis.

    Used by KV-cache implementations. Validates bounds to fail fast instead of
    silently corrupting memory.
    """
    t = src.shape[-2]
    if dst_offset < 0 or dst_offset + t > dst.shape[-2]:
        raise IndexError(
            f"block_copy out of range: dst_offset={dst_offset}, src_len={t}, dst_len={dst.shape[-2]}"
        )
    dst[..., dst_offset : dst_offset + t, :].copy_(src)
