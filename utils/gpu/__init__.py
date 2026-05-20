"""
GPU Utilities Module

This module contains GPU-specific utilities and CUDA kernel optimizations.
"""

from __future__ import annotations

__all__ = [
    'GPUUtils',
    'CUDAOptimizations',
    'OptimizedLayerNorm',
    'OptimizedRMSNorm',
    'EnhancedCUDAOptimizations',
]

_LAZY_IMPORTS = {
    'GPUUtils': '..gpu_utils',
    'CUDAOptimizations': '..cuda_kernels',
    'OptimizedLayerNorm': '..cuda_kernels',
    'OptimizedRMSNorm': '..cuda_kernels',
    'EnhancedCUDAOptimizations': '..enhanced_cuda_kernels',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for GPU utility modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=2)
        obj = getattr(module, name)
        _import_cache[name] = obj
        return obj
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


