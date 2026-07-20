"""
Optimization Techniques Package

This package contains advanced optimization techniques including computational
optimizations and Triton-based optimizations for GPU acceleration.
"""

from __future__ import annotations
import logging
from optimization_core.utils.dependency_manager import resolve_lazy_import

_logger = logging.getLogger(__name__)

_LAZY_IMPORTS = {
    'computational_optimizations': '.computational_optimizations',
    'triton_optimizations': '.triton_optimizations',
    'ComputationalOptimizer': '.computational_optimizations',
    'TritonOptimizer': '.triton_optimizations',
    'AdvancedRMSNorm': '.advanced_normalization',
    'AdvancedNormalizationOptimizations': '.advanced_normalization',
    'RotaryEmbedding': '.positional_encodings',
    'SwiGLU': '.enhanced_mlp',
    'RLPruning': '.rl_pruning',
    'TritonOptimizations': '.triton_optimizations',
    'PositionalEncodingOptimizations': '.positional_encodings',
}


def __getattr__(name: str):
    """Lazy import system for optimization techniques."""
    return resolve_lazy_import(name, __package__ or 'techniques', _LAZY_IMPORTS)


def __dir__():
    """Return list of available attributes."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    'computational_optimizations',
    'triton_optimizations',
    'ComputationalOptimizer',
    'TritonOptimizer',
    'AdvancedRMSNorm',
    'AdvancedNormalizationOptimizations',
    'RotaryEmbedding',
    'SwiGLU',
    'RLPruning',
    'TritonOptimizations',
    'PositionalEncodingOptimizations',
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"