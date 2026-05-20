"""
Production Optimizer Package

This package contains production-ready optimizer implementations for the
TruthGPT Optimization Core. It provides optimized versions of the core
algorithms for deployment in production environments.
"""

from __future__ import annotations
import logging
from optimization_core.utils.dependency_manager import resolve_lazy_import

_logger = logging.getLogger(__name__)

_LAZY_IMPORTS = {
    'create_production_optimizer': '.production_optimizer',
    'ProductionOptimizer': '.production_optimizer',
    'ProductionConfig': '.production_optimizer',
}


def __getattr__(name: str):
    """Lazy import system for production optimizer components."""
    return resolve_lazy_import(name, __package__ or 'production', _LAZY_IMPORTS)


def __dir__():
    """Return list of available attributes."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    'create_production_optimizer',
    'ProductionOptimizer',
    'ProductionConfig',
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"