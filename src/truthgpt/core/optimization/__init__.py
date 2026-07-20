"""
Optimization Cores Package

This package contains the core optimization engine implementations for the
TruthGPT Optimization Core. It provides the main optimization loop and
registry for available optimization strategies.
"""

from __future__ import annotations
import logging
from typing import Dict, Any

from .base_strategy import BaseOptimizationStrategy
from .unified_core import UnifiedOptimizationCore

from .enhanced_optimization_core import create_enhanced_optimization_core
from .hybrid_optimization_core import create_hybrid_optimization_core
from .mega_enhanced_optimization_core import create_mega_enhanced_optimization_core
from .supreme_optimization_core import create_supreme_optimization_core
from .transcendent_optimization_core import create_transcendent_optimization_core
from .ultra_enhanced_optimization_core import create_ultra_enhanced_optimization_core
from .ultra_fast_optimization_core import create_ultra_fast_optimization_core

_logger = logging.getLogger(__name__)

OPTIMIZATION_CORE_REGISTRY = {
    'enhanced': create_enhanced_optimization_core,
    'hybrid': create_hybrid_optimization_core,
    'mega_enhanced': create_mega_enhanced_optimization_core,
    'supreme': create_supreme_optimization_core,
    'transcendent': create_transcendent_optimization_core,
    'ultra_enhanced': create_ultra_enhanced_optimization_core,
    'ultra_fast': create_ultra_fast_optimization_core
}

def create_optimization_core(core_type: str, config: Dict[str, Any] = None) -> UnifiedOptimizationCore:
    """
    Factory method to create a unified optimization core with the specified strategy.
    """
    if config is None:
        config = {}
        
    if core_type not in OPTIMIZATION_CORE_REGISTRY:
        _logger.warning(f"Core type '{core_type}' not found, falling back to 'hybrid'.")
        core_type = 'hybrid'
        
    strategy_factory = OPTIMIZATION_CORE_REGISTRY[core_type]
    strategy = strategy_factory(config)
    
    return UnifiedOptimizationCore(strategy)

def list_available_cores() -> list[str]:
    """Return list of available optimization core strategies."""
    return list(OPTIMIZATION_CORE_REGISTRY.keys())

__all__ = [
    'create_optimization_core',
    'OPTIMIZATION_CORE_REGISTRY',
    'list_available_cores',
    'UnifiedOptimizationCore',
    'BaseOptimizationStrategy'
]

__version__ = "1.0.0"
__author__ = "TruthGPT Optimization Core Team"