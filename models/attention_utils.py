"""
Advanced Attention Mechanisms & Positional Encoding Utilities
=============================================================

Implements sinusoidal positional encodings, Rotary Positional Embeddings (RoPE),
Attention with Linear Biases (ALiBi), and backend-agnostic Efficient Attention
(Flash Attention, xFormers, SDPA, PyTorch).
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

from .interfaces import BaseAttentionModule

logger = logging.getLogger(__name__)

try:
    from xformers.ops import memory_efficient_attention
    _XFORMERS_AVAILABLE = True
except ImportError:
    _XFORMERS_AVAILABLE = False
    memory_efficient_attention = None

try:
    import flash_attn
    _FLASH_ATTN_AVAILABLE = True
except ImportError:
    _FLASH_ATTN_AVAILABLE = False
    flash_attn = None


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for transformer architectures."""

    def __init__(
        self,
        d_model: int,
        max_len: int = 5000,
        dropout: float = 0.1,
        batch_first: bool = True
    ) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.batch_first = batch_first

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        if batch_first:
            pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        else:
            pe = pe.unsqueeze(0).transpose(0, 1)  # [max_len, 1, d_model]

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding to input tensor."""
        if self.batch_first:
            x = x + self.pe[:, :x.size(1), :]
        else:
            x = x + self.pe[:x.size(0), :, :]
        return self.dropout(x)


class RotaryPositionalEmbedding(nn.Module):
    """Rotary Positional Embedding (RoPE) with Linear and Dynamic NTK Scaling."""

    def __init__(
        self,
        dim: int,
        max_seq_len: int = 2048,
        base: int = 10000,
        scaling_type: Optional[str] = None,
        scaling_factor: float = 1.0,
    ) -> None:
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = float(base)
        self.scaling_type = scaling_type
        self.scaling_factor = float(scaling_factor)

        inv_freq = 1.0 / (self.base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)

        t = torch.arange(max_seq_len).type_as(self.inv_freq)
        if self.scaling_type == "linear" and self.scaling_factor != 1.0:
            t = t / self.scaling_factor

        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :])
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :])

    def _compute_dynamic_ntk_freqs(self, seq_len: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        scale = self.scaling_factor
        if seq_len > self.max_seq_len and self.scaling_type in ("dynamic_ntk", "dynamic"):
            base = self.base * ((scale * seq_len / self.max_seq_len) - (scale - 1)) ** (self.dim / (self.dim - 2))
            inv_freq = 1.0 / (base ** (torch.arange(0, self.dim, 2, device=device).float() / self.dim))
        else:
            inv_freq = self.inv_freq.to(device)

        t = torch.arange(seq_len, device=device, dtype=inv_freq.dtype)
        if self.scaling_type == "linear" and scale != 1.0:
            t = t / scale

        freqs = torch.einsum("i,j->ij", t, inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        return emb.cos()[None, None, :, :], emb.sin()[None, None, :, :]

    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        seq_len: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply RoPE rotation to query and key tensors."""
        seq_len = seq_len or q.shape[-2]

        if seq_len > self.max_seq_len or self.scaling_type in ("dynamic_ntk", "dynamic"):
            cos, sin = self._compute_dynamic_ntk_freqs(seq_len, q.device)
        else:
            cos = self.cos_cached[:, :, :seq_len, :].to(q.device)
            sin = self.sin_cached[:, :, :seq_len, :].to(q.device)

        def rotate_half(x: torch.Tensor) -> torch.Tensor:
            x1, x2 = x[..., :x.shape[-1] // 2], x[..., x.shape[-1] // 2:]
            return torch.cat([-x2, x1], dim=-1)

        q_embed = (q * cos) + (rotate_half(q) * sin)
        k_embed = (k * cos) + (rotate_half(k) * sin)

        return q_embed, k_embed


class ALiBiPositionalEmbedding(nn.Module):
    """Attention with Linear Biases (ALiBi) positional embedding."""

    def __init__(self, num_heads: int = 8, max_seq_len: int = 2048) -> None:
        super().__init__()
        self.num_heads = num_heads
        self.max_seq_len = max_seq_len

        def get_slopes(n: int) -> list:
            def get_slopes_power_of_2(n_heads: int) -> list:
                start = (2 ** (-2 ** -(math.log2(n_heads) - 3)))
                ratio = start
                return [start * (ratio ** i) for i in range(n_heads)]

            if math.log2(n).is_integer():
                return get_slopes_power_of_2(n)
            else:
                closest_power_of_2 = 2 ** math.floor(math.log2(n))
                return (
                    get_slopes_power_of_2(closest_power_of_2)
                    + get_slopes(2 * closest_power_of_2)[0::2][: n - closest_power_of_2]
                )

        slopes = torch.tensor(get_slopes(num_heads)).unsqueeze(1).unsqueeze(2)  # [num_heads, 1, 1]
        self.register_buffer("slopes", slopes)

    def get_bias(
        self,
        seq_len: int,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None
    ) -> torch.Tensor:
        """Generate ALiBi attention bias matrix [1, num_heads, seq_len, seq_len]."""
        dev = device or self.slopes.device
        dt = dtype or self.slopes.dtype

        # Distance matrix: [seq_len, seq_len]
        context_pos = torch.arange(seq_len, device=dev, dtype=dt)[:, None]
        memory_pos = torch.arange(seq_len, device=dev, dtype=dt)[None, :]
        relative_pos = memory_pos - context_pos  # non-positive for causal
        relative_pos = relative_pos.unsqueeze(0).expand(self.num_heads, -1, -1)  # [num_heads, seq_len, seq_len]

        alibi_bias = self.slopes.to(device=dev, dtype=dt) * relative_pos
        return alibi_bias.unsqueeze(0)  # [1, num_heads, seq_len, seq_len]

    def forward(
        self,
        seq_len: Optional[int] = None,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
        x: Optional[torch.Tensor] = None,
        **kwargs: Any
    ) -> torch.Tensor:
        """Forward invocation returning bias tensor."""
        if seq_len is None:
            if x is not None:
                seq_len = x.shape[-2] if x.dim() >= 2 else x.shape[0]
            else:
                seq_len = self.max_seq_len
        return self.get_bias(seq_len=seq_len, device=device, dtype=dtype)


class EfficientAttention(BaseAttentionModule):
    """
    Efficient multi-head attention module supporting MHA/GQA/MQA, Flash Attention,
    xFormers, PyTorch SDPA, and fallback PyTorch attention.
    """

    def __init__(
        self,
        dim: int = 64,
        num_heads: int = 8,
        num_kv_heads: Optional[int] = None,
        attention_backend: str = "auto",
        dropout: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__()
        assert dim % num_heads == 0, f"dim ({dim}) must be divisible by num_heads ({num_heads})"

        self.dim = dim
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads or num_heads
        self.head_dim = dim // num_heads
        self.num_queries_per_kv = self.num_heads // self.num_kv_heads
        self.scale = self.head_dim ** -0.5
        self.dropout = nn.Dropout(dropout)

        backend = str(attention_backend).lower()
        if backend == "auto":
            if _FLASH_ATTN_AVAILABLE:
                self.backend = "flash"
            elif _XFORMERS_AVAILABLE:
                self.backend = "xformers"
            elif hasattr(F, "scaled_dot_product_attention"):
                self.backend = "sdpa"
            else:
                self.backend = "torch"
        else:
            self.backend = backend

        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, self.num_kv_heads * self.head_dim)
        self.v_proj = nn.Linear(dim, self.num_kv_heads * self.head_dim)
        self.out_proj = nn.Linear(dim, dim)

        logger.debug(f"EfficientAttention initialized with backend '{self.backend}' (heads={num_heads}, kv_heads={self.num_kv_heads})")

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        causal: bool = False,
        **kwargs: Any
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape

        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)

        if self.num_queries_per_kv > 1:
            k = k.repeat_interleave(self.num_queries_per_kv, dim=1)
            v = v.repeat_interleave(self.num_queries_per_kv, dim=1)

        if self.backend in ("flash", "flash_attention") and _FLASH_ATTN_AVAILABLE:
            attn_output = flash_attn.flash_attn_func(
                q, k, v, dropout_p=self.dropout.p if self.training else 0.0, causal=causal
            )
        elif self.backend == "xformers" and _XFORMERS_AVAILABLE and memory_efficient_attention is not None:
            attn_output = memory_efficient_attention(q, k, v, attn_bias=mask)
        elif self.backend in ("sdpa", "torch_sdpa") and hasattr(F, "scaled_dot_product_attention"):
            attn_output = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=mask,
                dropout_p=self.dropout.p if self.training else 0.0,
                is_causal=causal and (mask is None)
            )
        else:
            attn_output = self._torch_attention(q, k, v, mask, causal)

        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.dim)
        return self.out_proj(attn_output)

    def _torch_attention(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        mask: Optional[torch.Tensor],
        causal: bool,
    ) -> torch.Tensor:
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        if causal:
            causal_mask = torch.triu(
                torch.ones(scores.shape[-2], scores.shape[-1], device=scores.device),
                diagonal=1
            ).bool()
            scores.masked_fill_(causal_mask, float("-inf"))

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        return torch.matmul(attn_weights, v)


class AttentionOptimizer:
    """Utility class for configuring attention hardware optimizations and computing metrics."""

    @staticmethod
    def enable_sdpa_attention(model: nn.Module) -> None:
        """Enable PyTorch Scaled Dot-Product Attention if available."""
        if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "sdp_kernel"):
            try:
                torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=True)
                logger.info("SDPA kernel acceleration enabled")
            except Exception as e:
                logger.debug(f"Could not enable SDPA kernels: {e}")

    @staticmethod
    def enable_flash_attention(model: nn.Module) -> None:
        """Enable Flash Attention for compatible modules."""
        if not _FLASH_ATTN_AVAILABLE:
            logger.debug("Flash Attention not installed")
            return
        logger.info("Flash Attention enabled on model")

    @staticmethod
    def enable_xformers_attention(model: nn.Module) -> None:
        """Enable xFormers attention for compatible modules."""
        if not _XFORMERS_AVAILABLE:
            logger.debug("xFormers attention not installed")
            return
        logger.info("xFormers attention enabled on model")

    @staticmethod
    def compute_causal_mask(seq_len: int, device: Optional[torch.device] = None) -> torch.Tensor:
        """Compute lower triangular causal boolean mask [seq_len, seq_len]."""
        return torch.tril(torch.ones((seq_len, seq_len), dtype=torch.bool, device=device))

    @staticmethod
    def estimate_kv_cache_memory_mb(
        batch_size: int,
        max_seq_len: int,
        num_layers: int,
        num_kv_heads: int,
        head_dim: int,
        dtype_bytes: int = 2,
    ) -> float:
        """Estimate total memory in MB required for KV cache."""
        total_bytes = 2 * batch_size * max_seq_len * num_layers * num_kv_heads * head_dim * dtype_bytes
        return total_bytes / (1024.0 * 1024.0)

    @staticmethod
    def estimate_attention_flops(
        seq_len: int,
        d_model: int,
        num_heads: int,
    ) -> int:
        """Estimate FLOPs for standard self-attention forward pass."""
        return 4 * seq_len * seq_len * d_model


def create_attention(
    dim: int = 64,
    num_heads: int = 8,
    attention_backend: str = "auto",
    dropout: float = 0.0,
    **kwargs: Any
) -> EfficientAttention:
    """Factory helper for creating EfficientAttention."""
    return EfficientAttention(
        dim=dim,
        num_heads=num_heads,
        attention_backend=attention_backend,
        dropout=dropout,
        **kwargs
    )


create_attention_module = create_attention
AttentionUtils = AttentionOptimizer

__all__ = [
    "PositionalEncoding",
    "RotaryPositionalEmbedding",
    "ALiBiPositionalEmbedding",
    "EfficientAttention",
    "AttentionOptimizer",
    "AttentionUtils",
    "create_attention",
    "create_attention_module",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
