"""
GPU Utilities Module

GPU-specific utilities, CUDA kernel optimizations, and kernel fusion.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'GPUUtils',
    'CUDAOptimizations',
    'OptimizedLayerNorm',
    'OptimizedRMSNorm',
    'EnhancedCUDAOptimizations',
    'KernelFusion',
    'list_available_gpu_components',
    'get_gpu_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'GPUUtils': '.gpu_utils',
    'CUDAOptimizations': '.cuda_kernels',
    'OptimizedLayerNorm': '.cuda_kernels',
    'OptimizedRMSNorm': '.cuda_kernels',
    'EnhancedCUDAOptimizations': '.enhanced_cuda_kernels',
    'KernelFusion': '.kernel_fusion',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_gpu_components() -> List[str]:
    """List all available GPU utility components."""
    return _loader.list_components()


def get_gpu_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a GPU component."""
    return _loader.get_component_info(component_name)
