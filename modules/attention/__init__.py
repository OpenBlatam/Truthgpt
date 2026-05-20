"""
Attention module for TruthGPT Optimization Core
Contains multi-head attention and specialized attention implementations
"""

import logging

logger = logging.getLogger(__name__)

# Import Multi-Head Attention
try:
    from .multi_head_attention import (
        MultiHeadAttention,
        ScaledDotProductAttention,
        create_multi_head_attention,
        CrossAttention,
        create_cross_attention
    )
except ImportError as e:
    logger.warning(f"Multi-head attention components failed to load: {e}")
    MultiHeadAttention = None
    ScaledDotProductAttention = None
    create_multi_head_attention = None
    CrossAttention = None
    create_cross_attention = None

# Import Flash Attention
try:
    from .flash_attention import (
        FlashAttention,
        FlashAttentionV2,
        create_flash_attention
    )
except ImportError as e:
    logger.warning(f"Flash attention components failed to load: {e}")
    FlashAttention = None
    FlashAttentionV2 = None
    create_flash_attention = None

# Import Specialized Attention from attention.py
try:
    from .attention import (
        TruthGPTSparseAttention as SparseAttention,
        TruthGPTLocalAttention as LocalAttention,
        TruthGPTLinearAttention as LinearAttention,
        create_truthgpt_attention as create_sparse_attention
    )
    # Alias StridedAttention to SparseAttention if missing
    StridedAttention = SparseAttention
except ImportError as e:
    logger.warning(f"Specialized attention components failed to load: {e}")
    SparseAttention = None
    LocalAttention = None
    LinearAttention = None
    StridedAttention = None
    create_sparse_attention = None

__all__ = [
    # Multi-Head Attention
    'MultiHeadAttention',
    'ScaledDotProductAttention',
    'create_multi_head_attention',
    'CrossAttention',
    'create_cross_attention',
    
    # Flash Attention
    'FlashAttention',
    'FlashAttentionV2',
    'create_flash_attention',
    
    # Specialized Attention
    'SparseAttention',
    'LocalAttention',
    'StridedAttention',
    'LinearAttention',
    'create_sparse_attention'
]
