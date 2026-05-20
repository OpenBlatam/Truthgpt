"""
Core Optimizer Implementations

This package contains the core optimizer implementations for the TruthGPT
Optimization Core. It provides generic, production, and specialized optimizers.
"""

from __future__ import annotations
import logging
from optimization_core.utils.dependency_manager import resolve_lazy_import

_logger = logging.getLogger(__name__)

_LAZY_IMPORTS = {
    'create_generic_optimizer': '.generic_optimizer',
    'GenericOptimizer': '.generic_optimizer',
    'OptimizationConfig': '.generic_optimizer',
    'OptimizationResult': '.generic_optimizer',
}


def __getattr__(name: str):
    """Lazy import system for core optimizer components."""
    return resolve_lazy_import(name, __package__ or 'core', _LAZY_IMPORTS)


def __dir__():
    """Return list of available attributes."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    'create_generic_optimizer',
    'GenericOptimizer',
    'OptimizationConfig',
    'OptimizationResult',
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"