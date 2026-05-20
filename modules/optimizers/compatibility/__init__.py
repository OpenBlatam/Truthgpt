"""
Compatibility Shim Package

This package provides backward compatibility shims for the TruthGPT
Optimization Core. It ensures that legacy code can still use the
optimization_core package without modification.
"""

from __future__ import annotations
import logging
from optimization_core.utils.dependency_manager import resolve_lazy_import

_logger = logging.getLogger(__name__)

_LAZY_IMPORTS = {
    'generic_shims': '.generic_shims',
    'GenericShim': '.generic_shims',
    'create_shim': '.generic_shims',
}


def __getattr__(name: str):
    """Lazy import system for compatibility shims."""
    return resolve_lazy_import(name, __package__ or 'compatibility', _LAZY_IMPORTS)


def __dir__():
    """Return list of available attributes."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    'generic_shims',
    'GenericShim',
    'create_shim',
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"