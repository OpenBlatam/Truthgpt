"""
Memory Utilities Module

Memory optimization, pooling, activation caching, and tensor management.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'MemoryOptimizer',
    'MemoryOptimizationConfig',
    'create_memory_optimizer',
    'TensorPool',
    'ActivationCache',
    'MemoryPoolingOptimizer',
    'MemoryUtils',
    'list_available_memory_components',
    'get_memory_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'MemoryOptimizer': '.optimizations',
    'MemoryOptimizationConfig': '.optimizations',
    'create_memory_optimizer': '.optimizations',
    'TensorPool': '.pooling',
    'ActivationCache': '.pooling',
    'MemoryPoolingOptimizer': '.pooling',
    'MemoryUtils': '.memory_utils',
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


def list_available_memory_components() -> List[str]:
    """List all available memory utility components."""
    return _loader.list_components()


def get_memory_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a memory component."""
    return _loader.get_component_info(component_name)
