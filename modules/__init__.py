"""
Modules Package for TruthGPT Optimization Core
Modular system following deep learning best practices

This module provides organized access to module components:
- optimizers: Module optimizers (CUDA, GPU, Memory)
- advanced: Advanced optimization modules
- attention: Attention mechanisms
- embeddings: Embedding components
- feed_forward: Feed-forward networks
- model: Model components
- optimization: Optimization strategies
- training: Training components
- transformer: Transformer components
- learning: Learning strategies and optimization
"""

from __future__ import annotations

# All backward-compatibility components are handled via lazy imports

# Lazy imports for organized submodules
_LAZY_IMPORTS = {
    # Submodules
    'optimizers': '.optimizers',
    'advanced': '.advanced',
    'attention': '.attention',
    'embeddings': '.embeddings',
    'feed_forward': '.feed_forward',
    'model': '.model',
    'optimization': '.optimization',
    'training': '.training',
    'transformer': '.transformer',
    'base': '.base',
    'interface': '.interface',
    'memory': '.memory',
    'monitoring': '.monitoring',
    'learning': '.learning',
    
    # Advanced Libraries components
    'OptimizationConfig': '.advanced_libraries',
    'BaseOptimizer': '.advanced_libraries',
    'PerformanceMonitor': '.advanced_libraries',
    'ModelRegistry': '.advanced_libraries',
    'ConfigManager': '.advanced_libraries',
    'ExperimentTracker': '.advanced_libraries',
    'create_optimization_config': '.advanced_libraries',
    'create_performance_monitor': '.advanced_libraries',
    'create_model_registry': '.advanced_libraries',
    'create_config_manager': '.advanced_libraries',
    'create_experiment_tracker': '.advanced_libraries',
    
    # CUDA Optimizer components
    'CudaKernelConfig': '.cuda_optimizer',
    'CudaKernelType': '.cuda_optimizer',
    'CudaKernelOptimizer': '.cuda_optimizer',
    'CudaKernelManager': '.cuda_optimizer',
    'create_cuda_optimizer': '.cuda_optimizer',
    'create_cuda_kernel_manager': '.cuda_optimizer',
    'create_cuda_kernel_config': '.cuda_optimizer',
    
    # GPU Optimizer components
    'GPUOptimizationConfig': '.gpu_optimizer',
    'GPUOptimizationLevel': '.gpu_optimizer',
    'GPUOptimizer': '.gpu_optimizer',
    'GPUMemoryManager': '.gpu_optimizer',
    'create_gpu_optimizer': '.gpu_optimizer',
    'create_gpu_optimization_config': '.gpu_optimizer',
    'create_gpu_memory_manager': '.gpu_optimizer',
    
    # Memory Optimizer components
    'MemoryOptimizationConfig': '.memory_optimizer',
    'MemoryOptimizationLevel': '.memory_optimizer',
    'MemoryOptimizer': '.memory_optimizer',
    'MemoryProfiler': '.memory_optimizer',
    'create_memory_optimizer': '.memory_optimizer',
    'create_memory_optimization_config': '.memory_optimizer',
    'create_memory_profiler': '.memory_optimizer',
}

_import_cache = {}

def __getattr__(name: str):
    """Lazy import system for module submodules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=1)
        
        # If the requested name is not a submodule but a class/function inside it
        if hasattr(module, name):
            obj = getattr(module, name)
            _import_cache[name] = obj
            return obj
            
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e

def list_available_module_submodules() -> list[str]:
    """List all available module submodules."""
    return [k for k, v in _LAZY_IMPORTS.items() if not k[0].isupper() and not k.startswith('create_')]

__all__ = [
    # Advanced Libraries
    'OptimizationConfig',
    'BaseOptimizer',
    'PerformanceMonitor',
    'ModelRegistry',
    'ConfigManager',
    'ExperimentTracker',
    'create_optimization_config',
    'create_performance_monitor',
    'create_model_registry',
    'create_config_manager',
    'create_experiment_tracker',
    
    # CUDA Optimizer (backward compatible)
    'CudaKernelConfig',
    'CudaKernelType',
    'CudaKernelOptimizer',
    'CudaKernelManager',
    'create_cuda_optimizer',
    'create_cuda_kernel_manager',
    'create_cuda_kernel_config',
    
    # GPU Optimizer (backward compatible)
    'GPUOptimizationConfig',
    'GPUOptimizationLevel',
    'GPUOptimizer',
    'GPUMemoryManager',
    'create_gpu_optimizer',
    'create_gpu_optimization_config',
    'create_gpu_memory_manager',
    
    # Memory Optimizer (backward compatible)
    'MemoryOptimizationConfig',
    'MemoryOptimizationLevel',
    'MemoryOptimizer',
    'MemoryProfiler',
    'create_memory_optimizer',
    'create_memory_optimization_config',
    'create_memory_profiler',
    
    # Submodules
    'optimizers',
    'advanced',
    'attention',
    'embeddings',
    'feed_forward',
    'model',
    'optimization',
    'training',
    'transformer',
    'base',
    'interface',
    'memory',
    'monitoring',
    'learning',
    'list_available_module_submodules',
]

# Version information
__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"
__description__ = "Modular optimization system for TruthGPT following deep learning best practices"