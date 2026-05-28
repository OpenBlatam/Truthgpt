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
    'truthgpt': '.truthgpt',
    'optimizers': '.optimizers',
    'systems': '.systems',
    'training_tools': '.training_tools',
    'adapters': '.adapters',
    'ai': '.ai',
    'enterprise': '.enterprise',
    'gpu': '.gpu',
    'memory': '.memory',
    'monitoring': '.monitoring',
    'quantum': '.quantum',
    'training': '.training',
}

_OPTIONAL_ATTRS = {
    'visualize_checkpoints': ('.visualize_training', 'visualize_checkpoints'),
    'summarize_run': ('.visualize_training', 'summarize_run'),
    'compare_runs': ('.compare_runs', 'compare_runs'),
    'get_run_info': ('.compare_runs', 'get_run_info'),
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for utility submodules and optional training helpers."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name in _OPTIONAL_ATTRS:
        if name in _import_cache:
            return _import_cache[name]
        module_path, attr = _OPTIONAL_ATTRS[name]
        try:
            module = __import__(module_path, fromlist=[attr], level=1)
            value = getattr(module, attr)
            _import_cache[name] = value
            return value
        except (ImportError, AttributeError) as e:
            raise AttributeError(
                f"module '{__name__}' has no attribute '{name}'. Failed to import: {e}"
            ) from e
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=1)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
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
