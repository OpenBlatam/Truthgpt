"""
Unified TruthGPT Optimizers — Lazy Loading Edition
===================================================
Consolidated optimizer system with lazy loading for maximum boot performance.
"""

from __future__ import annotations
from typing import Dict, Any, List

_LAZY_IMPORTS = {
    'core': '.core',
    'truthgpt': '.truthgpt',
    'specialized': '.specialized',
    'optimization_cores': '.optimization_cores',
    'techniques': '.techniques',
    'compatibility': '.compatibility',
    'registries': '.registries',
    'kv_cache': '.kv_cache',
    'tensorflow': '.tensorflow',
    'quantum': '.quantum',
    'production': '.production',
}

_import_cache = {}

def __getattr__(name: str) -> Any:
    """Lazy import system for optimizer submodules and classes."""
    if name in _LAZY_IMPORTS:
        module_path = _LAZY_IMPORTS[name]
        try:
            import importlib
            module = importlib.import_module(module_path, __package__)
            _import_cache[name] = module
            return module
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Could not lazy-import submodule {name}: {e}")
    
    # Core class mappings
    class_map = {
        'ProductionOptimizer': ('.production.production_optimizer', 'ProductionOptimizer'),
        'UnifiedOptimizer': ('.core.unified_optimizer', 'UnifiedOptimizer'),
        'BaseTruthGPTOptimizer': ('.core.base_truthgpt_optimizer', 'BaseTruthGPTOptimizer'),
        'UnifiedTruthGPTOptimizer': ('.core.base_truthgpt_optimizer', 'UnifiedTruthGPTOptimizer'),
        'OptimizationLevel': ('.core.base_truthgpt_optimizer', 'OptimizationLevel'),
    }
    
    if name in class_map:
        module_path, class_name = class_map[name]
        try:
            import importlib
            module = importlib.import_module(module_path, __package__)
            val = getattr(module, class_name)
            _import_cache[name] = val
            return val
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Could not lazy-import {name} from {module_path}: {e}")

    raise AttributeError(f"module {__name__} has no attribute {name}")

def create_truthgpt_optimizer(level: str = "basic", config: Dict[str, Any] = None):
    """Factory function with deferred imports."""
    from .core.base_truthgpt_optimizer import OptimizationLevel, UnifiedTruthGPTOptimizer
    
    level_map = {
        'basic': OptimizationLevel.BASIC,
        'advanced': OptimizationLevel.ADVANCED,
        'expert': OptimizationLevel.EXPERT,
        'enterprise': OptimizationLevel.ENTERPRISE,
    }
    opt_level = level_map.get(level.lower(), OptimizationLevel.BASIC)
    return UnifiedTruthGPTOptimizer(config=config or {}, level=opt_level)

def create_production_optimizer(config: Dict[str, Any] = None):
    from .production.production_optimizer import ProductionOptimizer
    return ProductionOptimizer(config=config or {})

__all__ = list(_LAZY_IMPORTS.keys()) + [
    'ProductionOptimizer', 'UnifiedOptimizer', 'BaseTruthGPTOptimizer',
    'UnifiedTruthGPTOptimizer', 'OptimizationLevel', 'create_truthgpt_optimizer',
    'create_production_optimizer'
]
