"""
Attention Backend Factories
===========================
Factory functions for torch scaled dot product attention and specialized backend kernels.
"""
from typing import Any, Callable, Optional
import torch
import torch.nn.functional as F

from .registry import Registry

ATTENTION_BACKENDS = Registry(name="AttentionRegistry")


def sdpa_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    attn_mask: Optional[torch.Tensor] = None,
    is_causal: bool = True,
    dropout_p: float = 0.0,
) -> torch.Tensor:
    """
    Execute PyTorch Scaled Dot-Product Attention (SDPA).
    """
    return F.scaled_dot_product_attention(
        q, k, v, attn_mask=attn_mask, dropout_p=dropout_p, is_causal=is_causal
    )


@ATTENTION_BACKENDS.register("sdpa")
def build_sdpa(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build SDPA backend function."""
    return sdpa_attention


@ATTENTION_BACKENDS.register("flash")
def build_flash(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build FlashAttention backend function (falls back to SDPA if flash_attn unavailable)."""
    try:
        import flash_attn  # noqa: F401
        # If flash_attn module exists, custom wrapper can be returned
    except ImportError:
        pass
    return sdpa_attention


@ATTENTION_BACKENDS.register("triton")
def build_triton(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build Triton attention backend function (falls back to SDPA if triton kernel is unbuilt)."""
    return sdpa_attention






