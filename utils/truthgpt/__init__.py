"""
TruthGPT Utilities Module

This module contains TruthGPT-specific utilities and components.
"""

from __future__ import annotations

__all__ = [
    'OptimizationLevel',
    'DeviceType',
    'PrecisionType',
    'TruthGPTConfig',
    'BaseTruthGPTOptimizer',
    'TruthGPTDeviceManager',
    'TruthGPTPrecisionManager',
    'TruthGPTMemoryManager',
    'TruthGPTPerformanceManager',
    'TruthGPTAttentionOptimizer',
    'TruthGPTQuantizationOptimizer',
    'TruthGPTPruningOptimizer',
    'TruthGPTIntegratedOptimizer',
    'create_truthgpt_config',
    'create_truthgpt_optimizer',
    'quick_truthgpt_optimization',
    'truthgpt_optimization_context',
]

_LAZY_IMPORTS = {
    # Core components from truthgpt_core
    'OptimizationLevel': '..truthgpt_core',
    'DeviceType': '..truthgpt_core',
    'PrecisionType': '..truthgpt_core',
    'TruthGPTConfig': '..truthgpt_core',
    'BaseTruthGPTOptimizer': '..truthgpt_core',
    'TruthGPTDeviceManager': '..truthgpt_core',
    'TruthGPTPrecisionManager': '..truthgpt_core',
    'TruthGPTMemoryManager': '..truthgpt_core',
    'TruthGPTPerformanceManager': '..truthgpt_core',
    'TruthGPTAttentionOptimizer': '..truthgpt_core',
    'TruthGPTQuantizationOptimizer': '..truthgpt_core',
    'TruthGPTPruningOptimizer': '..truthgpt_core',
    'TruthGPTIntegratedOptimizer': '..truthgpt_core',
    'create_truthgpt_config': '..truthgpt_core',
    'create_truthgpt_optimizer': '..truthgpt_core',
    'quick_truthgpt_optimization': '..truthgpt_core',
    'truthgpt_optimization_context': '..truthgpt_core',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for TruthGPT utility modules."""
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


def list_available_truthgpt_components() -> list[str]:
    """List all available TruthGPT components."""
    return list(_LAZY_IMPORTS.keys())


def get_truthgpt_component_info(component_name: str) -> dict[str, any]:
    """Get information about a TruthGPT component."""
    if component_name not in _LAZY_IMPORTS:
        raise ValueError(f"Unknown TruthGPT component: {component_name}")
    
    return {
        'name': component_name,
        'module': _LAZY_IMPORTS[component_name],
        'available': component_name in _import_cache or True,
    }

