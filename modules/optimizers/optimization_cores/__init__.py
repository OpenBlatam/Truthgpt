"""
Optimization Cores Package

This package contains the core optimization engine implementations for the
TruthGPT Optimization Core. It provides the main optimization loop and
registry for available optimization strategies.
"""

from __future__ import annotations
import logging
from optimization_core.utils.dependency_manager import resolve_lazy_import

_logger = logging.getLogger(__name__)

_LAZY_IMPORTS = {
    'create_optimization_core': 'optimization_core.optimizers.optimization_cores',
    'OPTIMIZATION_CORE_REGISTRY': 'optimization_core.optimizers.optimization_cores',
    'list_available_cores': 'optimization_core.optimizers.optimization_cores',
    'OptimizationCore': 'optimization_core.optimizers.optimization_cores',
    'CoreConfig': 'optimization_core.optimizers.optimization_cores',
}


def __getattr__(name: str):
    """Lazy import system for optimization core components."""
    return resolve_lazy_import(name, __package__ or 'optimization_cores', _LAZY_IMPORTS)


def __dir__():
    """Return list of available attributes."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    'create_optimization_core',
    'OPTIMIZATION_CORE_REGISTRY',
    'list_available_cores',
    'OptimizationCore',
    'CoreConfig',
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"