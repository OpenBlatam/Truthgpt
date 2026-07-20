"""
Optimization Registries Module

This module contains optimization registry systems.
"""

from __future__ import annotations

__all__ = [
    # Registry modules will be imported here
]

_LAZY_IMPORTS = {
    'advanced_optimization_registry': '..advanced_optimization_registry',
    'advanced_optimization_registry_v2': '..advanced_optimization_registry_v2',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for registry modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=2)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def list_available_registries() -> list[str]:
    """List all available registry modules."""
    return list(_LAZY_IMPORTS.keys())

