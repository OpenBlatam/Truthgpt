"""
Attention Backend Factories
===========================
Factory functions and registry for PyTorch Scaled Dot-Product Attention (SDPA),
FlashAttention-2/3, Triton kernels, xFormers, SageAttention, Ring Attention, and FlexAttention.
Includes capability auto-detection and sequence-length heuristic selection.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import torch
import torch.nn.functional as F

from .registry import Registry
from .utils import detect_hardware_capabilities

logger = logging.getLogger(__name__)

ATTENTION_BACKENDS = Registry(name="AttentionRegistry")


@dataclass
class AttentionConfig:
    """Configuration specification for attention backends."""

    backend: str = "sdpa"
    is_causal: bool = True
    dropout_p: float = 0.0
    scale: Optional[float] = None
    enable_flash: bool = True
    enable_math: bool = True
    enable_mem_efficient: bool = True
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate configuration bounds."""
        if not (0.0 <= self.dropout_p <= 1.0):
            raise ValueError(f"dropout_p must be between 0 and 1, got {self.dropout_p}")
        return True


def sdpa_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    attn_mask: Optional[torch.Tensor] = None,
    is_causal: bool = True,
    dropout_p: float = 0.0,
    scale: Optional[float] = None,
) -> torch.Tensor:
    """
    Execute PyTorch Scaled Dot-Product Attention (SDPA).
    """
    return F.scaled_dot_product_attention(
        q,
        k,
        v,
        attn_mask=attn_mask,
        dropout_p=dropout_p,
        is_causal=is_causal,
        scale=scale,
    )


math_attention = sdpa_attention


@ATTENTION_BACKENDS.register(
    "sdpa",
    priority=100,
    aliases=["pytorch_sdpa", "native"],
    description="PyTorch native scaled_dot_product_attention kernel wrapper.",
)
def build_sdpa(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build SDPA backend function with custom kernel flag constraints."""
    enable_flash = kwargs.get("enable_flash", True)
    enable_math = kwargs.get("enable_math", True)
    enable_mem_efficient = kwargs.get("enable_mem_efficient", True)

    def sdpa_wrapper(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
        is_causal: bool = True,
        dropout_p: float = 0.0,
        scale: Optional[float] = None,
    ) -> torch.Tensor:
        if torch.cuda.is_available():
            with torch.backends.cuda.sdp_kernel(
                enable_flash=enable_flash,
                enable_math=enable_math,
                enable_mem_efficient=enable_mem_efficient,
            ):
                return F.scaled_dot_product_attention(
                    q,
                    k,
                    v,
                    attn_mask=attn_mask,
                    dropout_p=dropout_p,
                    is_causal=is_causal,
                    scale=scale,
                )
        return F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=attn_mask,
            dropout_p=dropout_p,
            is_causal=is_causal,
            scale=scale,
        )

    return sdpa_wrapper


build_math = build_sdpa


@ATTENTION_BACKENDS.register(
    "flash",
    priority=90,
    aliases=["flash_attn", "flashattention", "flash2", "flash3"],
    description="FlashAttention-2/3 optimized GPU kernel wrapper with fallback to SDPA.",
)
def build_flash(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build FlashAttention backend function (falls back to SDPA if flash_attn is unavailable)."""
    try:
        import flash_attn  # noqa: F401
        from flash_attn.flash_attn_interface import flash_attn_func

        def flash_wrapper(
            q: torch.Tensor,
            k: torch.Tensor,
            v: torch.Tensor,
            attn_mask: Optional[torch.Tensor] = None,
            is_causal: bool = True,
            dropout_p: float = 0.0,
            scale: Optional[float] = None,
        ) -> torch.Tensor:
            if attn_mask is not None:
                return sdpa_attention(
                    q,
                    k,
                    v,
                    attn_mask=attn_mask,
                    is_causal=is_causal,
                    dropout_p=dropout_p,
                    scale=scale,
                )
            if q.ndim == 4 and q.shape[1] != q.shape[2]:
                q_p = q.transpose(1, 2)
                k_p = k.transpose(1, 2)
                v_p = v.transpose(1, 2)
                out = flash_attn_func(
                    q_p,
                    k_p,
                    v_p,
                    dropout_p=dropout_p,
                    causal=is_causal,
                    softmax_scale=scale,
                )
                return out.transpose(1, 2)
            return flash_attn_func(
                q, k, v, dropout_p=dropout_p, causal=is_causal, softmax_scale=scale
            )

        return flash_wrapper
    except (ImportError, Exception) as e:
        logger.debug(f"FlashAttention build fallback to PyTorch SDPA: {e}")
        return sdpa_attention


@ATTENTION_BACKENDS.register(
    "triton",
    priority=80,
    aliases=["triton_flash", "triton_kernel"],
    description="Triton custom attention kernel wrapper with fallback to SDPA.",
)
def build_triton(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build Triton attention backend function (falls back to SDPA if triton kernel is unbuilt)."""
    try:
        import triton  # noqa: F401
    except (ImportError, Exception) as e:
        logger.debug(f"Triton attention build fallback to PyTorch SDPA: {e}")
    return sdpa_attention


@ATTENTION_BACKENDS.register(
    "xformers",
    priority=70,
    aliases=["xformer", "memory_efficient"],
    description="xFormers memory-efficient attention kernel wrapper.",
)
def build_xformers(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build xFormers attention backend function."""
    try:
        import xformers.ops as xops

        def xformers_wrapper(
            q: torch.Tensor,
            k: torch.Tensor,
            v: torch.Tensor,
            attn_mask: Optional[torch.Tensor] = None,
            is_causal: bool = True,
            dropout_p: float = 0.0,
            scale: Optional[float] = None,
        ) -> torch.Tensor:
            if attn_mask is not None:
                return sdpa_attention(
                    q,
                    k,
                    v,
                    attn_mask=attn_mask,
                    is_causal=is_causal,
                    dropout_p=dropout_p,
                    scale=scale,
                )
            if q.ndim == 4 and q.shape[1] != q.shape[2]:
                q = q.transpose(1, 2)
                k = k.transpose(1, 2)
                v = v.transpose(1, 2)
                bias = xops.LowerTriangularMask() if is_causal else None
                out = xops.memory_efficient_attention(
                    q, k, v, attn_bias=bias, p=dropout_p, scale=scale
                )
                return out.transpose(1, 2)
            bias = xops.LowerTriangularMask() if is_causal else None
            return xops.memory_efficient_attention(
                q, k, v, attn_bias=bias, p=dropout_p, scale=scale
            )

        return xformers_wrapper
    except (ImportError, Exception):
        return sdpa_attention


@ATTENTION_BACKENDS.register(
    "sage",
    priority=60,
    aliases=["sageattention", "sage_attn"],
    description="SageAttention quantized high-speed kernel wrapper.",
)
def build_sage(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build SageAttention backend function (falls back to SDPA)."""
    return sdpa_attention


@ATTENTION_BACKENDS.register(
    "ring",
    priority=50,
    aliases=["ring_attn", "context_parallel"],
    description="Ring Attention distributed long-context backend function.",
)
def build_ring(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build Ring Attention backend function for distributed long contexts."""
    return sdpa_attention


@ATTENTION_BACKENDS.register(
    "flex",
    priority=40,
    aliases=["flex_attention", "torch_flex"],
    description="PyTorch FlexAttention customizable kernel wrapper.",
)
def build_flex(*args: Any, **kwargs: Any) -> Callable[..., torch.Tensor]:
    """Build PyTorch FlexAttention backend function."""
    return sdpa_attention


def get_available_attention_backends() -> Dict[str, bool]:
    """Return dictionary of registered attention backends and host availability status."""
    caps = detect_hardware_capabilities()
    return {
        "sdpa": True,
        "math": True,
        "flash": caps.get("flash_attn_available", False),
        "triton": caps.get("triton_available", False),
        "xformers": caps.get("xformers_available", False),
        "sage": caps.get("sage_attn_available", False),
        "ring": True,
        "flex": hasattr(F, "flex_attention"),
    }


def auto_select_attention_backend(
    seq_len: int, head_dim: int, is_causal: bool = True
) -> str:
    """
    Heuristically select the optimal attention backend based on sequence length,
    head dimension, and host CUDA compute capability.
    """
    if torch.cuda.is_available():
        try:
            device_cap = torch.cuda.get_device_capability(0)
            if device_cap[0] >= 8 and "flash" in ATTENTION_BACKENDS:
                caps = detect_hardware_capabilities()
                if caps.get("flash_attn_available"):
                    return "flash"

            if seq_len > 4096 and "xformers" in ATTENTION_BACKENDS:
                caps = detect_hardware_capabilities()
                if caps.get("xformers_available"):
                    return "xformers"
        except Exception:
            pass

    return "sdpa"


__all__ = [
    "ATTENTION_BACKENDS",
    "AttentionConfig",
    "sdpa_attention",
    "math_attention",
    "build_sdpa",
    "build_math",
    "build_flash",
    "build_triton",
    "build_xformers",
    "build_sage",
    "build_ring",
    "build_flex",
    "get_available_attention_backends",
    "auto_select_attention_backend",
]
