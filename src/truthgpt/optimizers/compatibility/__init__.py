"""
Compatibility Module

This module contains compatibility layers and utilities.
"""

from __future__ import annotations

__all__ = [
    # Compatibility modules will be imported here
]

_LAZY_IMPORTS = {
    'compatibility': '..compatibility',
    'generic_compatibility': '..generic_compatibility',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for compatibility modules."""
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


def list_available_compatibility_modules() -> list[str]:
    """List all available compatibility modules."""
    return list(_LAZY_IMPORTS.keys())

