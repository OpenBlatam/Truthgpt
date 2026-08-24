"""
Utilities for optimization_core.

This module provides organized access to various utility modules:
- truthgpt: TruthGPT-specific utilities
- optimizers: Optimizer utilities and engines
- systems: System-level utilities and integrations
- training_tools: Training monitoring and visualization tools
- adapters: Adapter utilities
- ai: AI/ML optimization utilities
- enterprise: Enterprise-grade utilities
- gpu: GPU utilities
- memory: Memory optimization utilities
- monitoring: Monitoring utilities
- quantum: Quantum computing utilities
- training: Training utilities
"""

from __future__ import annotations

# Lazy imports for organized submodules and optional training tools
_LAZY_IMPORTS = {
    # Submodules
    'adapters': '.adapters',
    'ai': '.ai',
    'deployment': '.deployment',
    'enterprise': '.enterprise',
    'gpu': '.gpu',
    'memory': '.memory',
    'modules': '.modules',
    'monitoring': '.monitoring',
    'networking': '.networking',
    'optimizers': '.optimizers',
    'performance': '.performance',
    'quantum': '.quantum',
    'resilience': '.resilience',
    'storage': '.storage',
    'systems': '.systems',
    'tests': '.tests',
    'training': '.training',
    'training_tools': '.training_tools',
    'truthgpt': '.truthgpt',
    'ultra': '.ultra',
    'validation': '.validation',
    
    # Commonly accessed utility classes directly from performance
    'OptimizationRegistry': '.performance.optimization_registry',
    'apply_optimizations': '.performance.optimization_registry',
    'get_optimization_config': '.performance.optimization_registry',
    'register_optimization': '.performance.optimization_registry',
}

_OPTIONAL_ATTRS = {
    'visualize_checkpoints': ('.visualize_training', 'visualize_checkpoints'),
    'summarize_run': ('.visualize_training', 'summarize_run'),
    'compare_runs': ('.compare_runs', 'compare_runs'),
    'get_run_info': ('.compare_runs', 'get_run_info'),
    'get_utility_registry': ('.registry', 'get_utility_registry'),
    'UtilityRegistry': ('.registry', 'UtilityRegistry'),
    'UTILITY_REGISTRY': ('.registry', 'UTILITY_REGISTRY'),
    'BaseUtility': ('.interfaces', 'BaseUtility'),
    'UtilityPipeline': ('.builder', 'UtilityPipeline'),
    'UtilityPipelineBuilder': ('.builder', 'UtilityPipelineBuilder'),
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for utility submodules and optional training helpers."""
    if name.startswith('_'):
        raise AttributeError(f"module has no attribute '{name}'")

    if name in _OPTIONAL_ATTRS:
        if name in _import_cache:
            return _import_cache[name]
        module_path, attr = _OPTIONAL_ATTRS[name]
        try:
            import importlib
            module = importlib.import_module(module_path, __package__)
            value = getattr(module, attr)
            _import_cache[name] = value
            return value
        except (ImportError, AttributeError) as e:
            raise AttributeError(
                f"Failed to import '{name}' from '{module_path}': {e}"
            ) from e
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        import importlib
        module = importlib.import_module(module_path, __package__)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"Failed to import '{name}' from '{module_path}': {e}"
        ) from e


def list_available_utility_modules() -> list[str]:
    """List all available utility submodules."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    "visualize_checkpoints",
    "summarize_run",
    "compare_runs",
    "get_run_info",
    "truthgpt",
    "optimizers",
    "systems",
    "training_tools",
    "adapters",
    "ai",
    "enterprise",
    "gpu",
    "memory",
    "monitoring",
    "quantum",
    "training",
    "list_available_utility_modules",
]
