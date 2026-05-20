"""
Module Optimizers

This module contains optimizer components for the modules package.
"""

from __future__ import annotations

__all__ = [
    'CudaKernelOptimizer',
    'CudaKernelConfig',
    'CudaKernelType',
    'CudaKernelManager',
    'create_cuda_optimizer',
    'create_cuda_kernel_manager',
    'create_cuda_kernel_config',
    'GPUOptimizer',
    'GPUOptimizationConfig',
    'GPUOptimizationLevel',
    'GPUMemoryManager',
    'create_gpu_optimizer',
    'create_gpu_optimization_config',
    'create_gpu_memory_manager',
    'MemoryOptimizer',
    'MemoryOptimizationConfig',
    'MemoryOptimizationLevel',
    'MemoryProfiler',
    'create_memory_optimizer',
    'create_memory_optimization_config',
    'create_memory_profiler',
    'create_module_optimizer',
    'list_available_module_optimizers',
    'get_module_optimizer_info',
    'MODULE_OPTIMIZER_REGISTRY',
]

_LAZY_IMPORTS = {
    # CUDA Optimizer
    'CudaKernelOptimizer': '..cuda_optimizer',
    'CudaKernelConfig': '..cuda_optimizer',
    'CudaKernelType': '..cuda_optimizer',
    'CudaKernelManager': '..cuda_optimizer',
    'create_cuda_optimizer': '..cuda_optimizer',
    'create_cuda_kernel_manager': '..cuda_optimizer',
    'create_cuda_kernel_config': '..cuda_optimizer',
    # GPU Optimizer
    'GPUOptimizer': '..gpu_optimizer',
    'GPUOptimizationConfig': '..gpu_optimizer',
    'GPUOptimizationLevel': '..gpu_optimizer',
    'GPUMemoryManager': '..gpu_optimizer',
    'create_gpu_optimizer': '..gpu_optimizer',
    'create_gpu_optimization_config': '..gpu_optimizer',
    'create_gpu_memory_manager': '..gpu_optimizer',
    # Memory Optimizer
    'MemoryOptimizer': '..memory_optimizer',
    'MemoryOptimizationConfig': '..memory_optimizer',
    'MemoryOptimizationLevel': '..memory_optimizer',
    'MemoryProfiler': '..memory_optimizer',
    'create_memory_optimizer': '..memory_optimizer',
    'create_memory_optimization_config': '..memory_optimizer',
    'create_memory_profiler': '..memory_optimizer',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for module optimizer components."""
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


def create_module_optimizer(optimizer_type: str = "cuda", config: dict = None):
    """
    Unified factory function to create module optimizers.
    
    Args:
        optimizer_type: Type of optimizer. Options: "cuda", "gpu", "memory"
        config: Optional configuration dictionary
    
    Returns:
        The requested optimizer instance
    """
    if config is None:
        config = {}
    
    optimizer_type = optimizer_type.lower()
    
    # Import functions lazily
    if optimizer_type == "cuda":
        from ..cuda_optimizer import create_cuda_optimizer
        return create_cuda_optimizer(config)
    elif optimizer_type == "gpu":
        from ..gpu_optimizer import create_gpu_optimizer
        return create_gpu_optimizer(config)
    elif optimizer_type == "memory":
        from ..memory_optimizer import create_memory_optimizer
        return create_memory_optimizer(config)
    else:
        available = ", ".join(["cuda", "gpu", "memory"])
        raise ValueError(
            f"Unknown module optimizer type: '{optimizer_type}'. "
            f"Available types: {available}"
        )


MODULE_OPTIMIZER_REGISTRY = {
    "cuda": {
        "module": "modules.cuda_optimizer",
        "factory": "create_cuda_optimizer",
    },
    "gpu": {
        "module": "modules.gpu_optimizer",
        "factory": "create_gpu_optimizer",
    },
    "memory": {
        "module": "modules.memory_optimizer",
        "factory": "create_memory_optimizer",
    },
}


def list_available_module_optimizers() -> list[str]:
    """List all available module optimizer types."""
    return list(MODULE_OPTIMIZER_REGISTRY.keys())


def get_module_optimizer_info(optimizer_type: str) -> dict[str, any]:
    """Get information about a module optimizer."""
    if optimizer_type not in MODULE_OPTIMIZER_REGISTRY:
        raise ValueError(f"Unknown module optimizer: {optimizer_type}")
    
    return {
        'name': optimizer_type,
        'module': MODULE_OPTIMIZER_REGISTRY[optimizer_type]['module'],
        'factory': MODULE_OPTIMIZER_REGISTRY[optimizer_type]['factory'],
    }

