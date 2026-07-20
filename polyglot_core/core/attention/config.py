from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Tuple
import numpy as np
import math
import time
from .backend import Backend, get_best_backend, is_backend_available

from .constants import *


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS AND CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class AttentionPattern(Enum):
    """Attention pattern types."""
    FULL = "full"              # Full O(N²) attention
    CAUSAL = "causal"          # Autoregressive causal mask
    SLIDING_WINDOW = "sliding" # Local sliding window
    SPARSE = "sparse"          # Block-sparse
    BIGBIRD = "bigbird"        # BigBird-style



class PositionEncoding(Enum):
    """Position encoding types."""
    NONE = "none"
    ROPE = "rope"       # Rotary Position Embeddings
    ALIBI = "alibi"     # Attention with Linear Biases
    RELATIVE = "relative"

class AttentionConfig:
    """
    Configuration for attention mechanisms.
    
    Attributes:
        d_model: Model dimension
        n_heads: Number of attention heads
        n_kv_heads: Number of key-value heads (for GQA, default: n_heads)
        head_dim: Dimension per head (default: d_model // n_heads)
        max_seq_len: Maximum sequence length
        dropout: Dropout probability
        pattern: Attention pattern type
        position_encoding: Position encoding type
        use_causal_mask: Whether to use causal mask
        window_size: Window size for sliding window attention
        block_size: Block size for Flash Attention tiling
        rope_theta: Base frequency for RoPE
    """
    d_model: int = DEFAULT_D_MODEL
    n_heads: int = DEFAULT_N_HEADS
    n_kv_heads: Optional[int] = None  # For Grouped-Query Attention (GQA)
    head_dim: Optional[int] = None
    max_seq_len: int = DEFAULT_MAX_SEQ_LEN
    dropout: float = DEFAULT_DROPOUT
    pattern: AttentionPattern = AttentionPattern.FULL
    position_encoding: PositionEncoding = PositionEncoding.NONE
    use_causal_mask: bool = False
    window_size: int = DEFAULT_WINDOW_SIZE
    block_size: int = DEFAULT_BLOCK_SIZE
    rope_theta: float = DEFAULT_ROPE_THETA
    
    def __post_init__(self):
        """Validate and set default values."""
        # Validate parameters
        if self.d_model <= 0:
            raise ValueError(f"d_model must be positive, got {self.d_model}")
        if self.n_heads <= 0:
            raise ValueError(f"n_heads must be positive, got {self.n_heads}")
        if self.d_model % self.n_heads != 0:
            raise ValueError(
                f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"
            )
        if self.max_seq_len <= 0:
            raise ValueError(f"max_seq_len must be positive, got {self.max_seq_len}")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError(f"dropout must be in [0, 1), got {self.dropout}")
        if self.window_size <= 0:
            raise ValueError(f"window_size must be positive, got {self.window_size}")
        if self.block_size <= 0:
            raise ValueError(f"block_size must be positive, got {self.block_size}")
        if self.rope_theta <= 0:
            raise ValueError(f"rope_theta must be positive, got {self.rope_theta}")
        
        # Set defaults
        if self.n_kv_heads is None:
            self.n_kv_heads = self.n_heads
        if self.head_dim is None:
            self.head_dim = self.d_model // self.n_heads
        
        # Validate GQA configuration
        if self.n_kv_heads > self.n_heads:
            raise ValueError(
                f"n_kv_heads ({self.n_kv_heads}) cannot be > n_heads ({self.n_heads})"
            )
        if self.n_heads % self.n_kv_heads != 0:
            raise ValueError(
                f"n_heads ({self.n_heads}) must be divisible by n_kv_heads ({self.n_kv_heads})"
            )
    
    @property
    def is_gqa(self) -> bool:
        """
        Check if using Grouped-Query Attention (GQA).
        
        Returns:
            True if n_kv_heads < n_heads
        """
        return self.n_kv_heads < self.n_heads
    
    @property
    def softmax_scale(self) -> float:
        """
        Get softmax scaling factor (1 / sqrt(head_dim)).
        
        Returns:
            Scaling factor for attention scores
        """
        return 1.0 / math.sqrt(self.head_dim)
    
    @classmethod
    def llama_7b(cls) -> "AttentionConfig":
        """
        Config for LLaMA 7B model.
        
        Returns:
            AttentionConfig with LLaMA 7B parameters
        """
        return cls(
            d_model=4096,
            n_heads=32,
            n_kv_heads=32,
            pattern=AttentionPattern.CAUSAL,
            position_encoding=PositionEncoding.ROPE
        )
    
    @classmethod
    def llama_70b(cls) -> "AttentionConfig":
        """
        Config for LLaMA 70B model with GQA.
        
        Returns:
            AttentionConfig with LLaMA 70B parameters (8 KV heads for 64 query heads)
        """
        return cls(
            d_model=8192,
            n_heads=64,
            n_kv_heads=8,
            pattern=AttentionPattern.CAUSAL,
            position_encoding=PositionEncoding.ROPE
        )
    
    @classmethod
    def mistral_7b(cls) -> "AttentionConfig":
        """
        Config for Mistral 7B model with sliding window.
        
        Returns:
            AttentionConfig with Mistral 7B parameters
        """
        return cls(
            d_model=4096,
            n_heads=32,
            n_kv_heads=8,
            pattern=AttentionPattern.SLIDING_WINDOW,
            window_size=4096,
            position_encoding=PositionEncoding.ROPE
        )

