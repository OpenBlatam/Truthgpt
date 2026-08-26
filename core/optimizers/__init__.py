"""
Core Optimizers
===============
Unified entry point for all optimizers in the optimization framework.
Features high-performance thread-safe lazy loading to avoid overhead during import.
"""

from __future__ import annotations

import sys
import importlib
import threading
from typing import Dict, Any, List, Optional, Callable

# ---------------------------------------------------------------------------
# Lazy Imports Mapping
# ---------------------------------------------------------------------------

_LAZY_OPTIMIZER_MAP: Dict[str, tuple[str, str]] = {
    # Ops optimizers
    "ExtremeOptimizer": ("..ops.extreme_optimizer", "ExtremeOptimizer"),
    "ExtremeOptimizationLevel": ("..ops.extreme_optimizer", "ExtremeOptimizationLevel"),
    "ExtremeOptimizationResult": ("..ops.extreme_optimizer", "ExtremeOptimizationResult"),
    "QuantumNeuralOptimizer": ("..ops.extreme_optimizer", "QuantumNeuralOptimizer"),
    "CosmicOptimizer": ("..ops.extreme_optimizer", "CosmicOptimizer"),
    "TranscendentOptimizer": ("..ops.extreme_optimizer", "TranscendentOptimizer"),
    "QuantumOptimizer": ("..ops.quantum_extreme_optimizer", "QuantumOptimizer"),
    "UltraFastOptimizer": ("..ops.ultra_fast_optimizer", "UltraFastOptimizer"),
    "ParallelOptimizer": ("..ops.ultra_fast_optimizer", "ParallelOptimizer"),
    "CacheOptimizer": ("..ops.ultra_fast_optimizer", "CacheOptimizer"),
    # Util optimizers
    "EnhancedOptimizer": ("..util.enhanced_optimizer", "EnhancedOptimizer"),
    "EnhancedOptimizationLevel": ("..util.enhanced_optimizer", "EnhancedOptimizationLevel"),
    "EnhancedOptimizationResult": ("..util.enhanced_optimizer", "EnhancedOptimizationResult"),
    "ComplementaryOptimizer": ("..util.complementary_optimizer", "ComplementaryOptimizer"),
    "ComplementaryOptimizationLevel": ("..util.complementary_optimizer", "ComplementaryOptimizationLevel"),
    "ComplementaryOptimizationResult": ("..util.complementary_optimizer", "ComplementaryOptimizationResult"),
    "AdvancedComplementaryOptimizer": ("..util.advanced_complementary_optimizer", "AdvancedComplementaryOptimizer"),
    "MicroservicesOptimizer": ("..util.microservices_optimizer", "MicroservicesOptimizer"),
    "OptimizerService": ("..util.microservices_optimizer", "OptimizerService"),
    # Framework optimizers
    "AIExtremeOptimizer": ("..framework.ai_extreme_optimizer", "AIExtremeOptimizer"),
    # Advanced optimizations
    "QuantumInspiredOptimizer": (".advanced_optimizations", "QuantumInspiredOptimizer"),
    "EvolutionaryOptimizer": (".advanced_optimizations", "EvolutionaryOptimizer"),
    "MetaLearningOptimizer": (".advanced_optimizations", "MetaLearningOptimizer"),
    # Core optimizers
    "BaseTruthGPTOptimizer": (".base_truthgpt_optimizer", "BaseTruthGPTOptimizer"),
    "UnifiedTruthGPTOptimizer": (".unified_optimizer", "UnifiedTruthGPTOptimizer"),
    "ModernTruthGPTOptimizer": (".modern_truthgpt_optimizer", "ModernTruthGPTOptimizer"),
    "ModularOptimizer": (".modular_optimizer", "ModularOptimizer"),
    "PyTorchOptimizerBase": (".pytorch_optimizer_base", "PyTorchOptimizerBase"),
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """Lazy import system for optimizer classes."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]

        if name in _LAZY_OPTIMIZER_MAP:
            mod_rel_path, symbol_name = _LAZY_OPTIMIZER_MAP[name]
            try:
                mod = importlib.import_module(mod_rel_path, package=__name__)
                obj = getattr(mod, symbol_name)
                _import_cache[name] = obj
                globals()[name] = obj
                return obj
            except Exception as e:
                raise AttributeError(f"Failed to lazy load '{name}' from '{mod_rel_path}': {e}") from e

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Return available symbols including lazy-loaded optimizers."""
    return sorted(list(set(globals().keys()) | set(_LAZY_OPTIMIZER_MAP.keys()) | set(__all__)))


# ---------------------------------------------------------------------------
# Metadata Registry & Factory
# ---------------------------------------------------------------------------

CORE_OPTIMIZER_REGISTRY: Dict[str, Dict[str, str]] = {
    "extreme": {
        "class": "ExtremeOptimizer",
        "module": "core.ops.extreme_optimizer",
    },
    "quantum": {
        "class": "QuantumOptimizer",
        "module": "core.ops.quantum_extreme_optimizer",
    },
    "ultra_fast": {
        "class": "UltraFastOptimizer",
        "module": "core.ops.ultra_fast_optimizer",
    },
    "enhanced": {
        "class": "EnhancedOptimizer",
        "module": "core.util.enhanced_optimizer",
    },
    "complementary": {
        "class": "ComplementaryOptimizer",
        "module": "core.util.complementary_optimizer",
    },
    "advanced_complementary": {
        "class": "AdvancedComplementaryOptimizer",
        "module": "core.util.advanced_complementary_optimizer",
    },
    "microservices": {
        "class": "MicroservicesOptimizer",
        "module": "core.util.microservices_optimizer",
    },
    "ai_extreme": {
        "class": "AIExtremeOptimizer",
        "module": "core.framework.ai_extreme_optimizer",
    },
    "quantum_inspired": {
        "class": "QuantumInspiredOptimizer",
        "module": "core.optimizers.advanced_optimizations",
    },
    "evolutionary": {
        "class": "EvolutionaryOptimizer",
        "module": "core.optimizers.advanced_optimizations",
    },
    "meta_learning": {
        "class": "MetaLearningOptimizer",
        "module": "core.optimizers.advanced_optimizations",
    },
    "modern_truthgpt": {
        "class": "ModernTruthGPTOptimizer",
        "module": "core.optimizers.modern_truthgpt_optimizer",
    },
    "modular": {
        "class": "ModularOptimizer",
        "module": "core.optimizers.modular_optimizer",
    },
    "base": {
        "class": "BaseTruthGPTOptimizer",
        "module": "core.optimizers.base_truthgpt_optimizer",
    },
    "unified": {
        "class": "UnifiedTruthGPTOptimizer",
        "module": "core.optimizers.unified_optimizer",
    },
}


def list_available_core_optimizers() -> List[str]:
    """List all available core optimizer types."""
    return list(CORE_OPTIMIZER_REGISTRY.keys())


def get_core_optimizer_info(optimizer_type: str) -> Dict[str, str]:
    """Get information about a specific core optimizer."""
    opt_type = optimizer_type.lower()
    if opt_type not in CORE_OPTIMIZER_REGISTRY:
        raise ValueError(f"Unknown optimizer type: '{optimizer_type}'")

    entry = CORE_OPTIMIZER_REGISTRY[opt_type]
    return {
        "type": opt_type,
        "class": entry["class"],
        "module": entry["module"],
    }


def create_core_optimizer(optimizer_type: str = "enhanced", config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Unified factory function to create core optimizers on demand.
    
    Args:
        optimizer_type: Type of optimizer to create.
        config: Optional configuration dictionary.
        
    Returns:
        The requested optimizer instance.
    """
    if config is None:
        config = {}

    opt_key = optimizer_type.lower()
    if opt_key not in CORE_OPTIMIZER_REGISTRY:
        available = ", ".join(sorted(CORE_OPTIMIZER_REGISTRY.keys()))
        raise ValueError(f"Unknown core optimizer type: '{optimizer_type}'. Available types: {available}")

    entry = CORE_OPTIMIZER_REGISTRY[opt_key]
    cls_name = entry["class"]
    cls_obj = getattr(sys.modules[__name__], cls_name)
    return cls_obj(config)


__all__ = [
    # Ops optimizers
    "ExtremeOptimizer",
    "ExtremeOptimizationLevel",
    "ExtremeOptimizationResult",
    "QuantumNeuralOptimizer",
    "CosmicOptimizer",
    "TranscendentOptimizer",
    "QuantumOptimizer",
    "UltraFastOptimizer",
    "ParallelOptimizer",
    "CacheOptimizer",
    # Util optimizers
    "EnhancedOptimizer",
    "EnhancedOptimizationLevel",
    "EnhancedOptimizationResult",
    "ComplementaryOptimizer",
    "ComplementaryOptimizationLevel",
    "ComplementaryOptimizationResult",
    "AdvancedComplementaryOptimizer",
    "MicroservicesOptimizer",
    "OptimizerService",
    # Framework optimizers
    "AIExtremeOptimizer",
    # Advanced optimizations
    "QuantumInspiredOptimizer",
    "EvolutionaryOptimizer",
    "MetaLearningOptimizer",
    # Core optimizers
    "ModernTruthGPTOptimizer",
    "ModularOptimizer",
    "PyTorchOptimizerBase",
    "BaseTruthGPTOptimizer",
    "UnifiedTruthGPTOptimizer",
    # Factory & Registry
    "create_core_optimizer",
    "CORE_OPTIMIZER_REGISTRY",
    "list_available_core_optimizers",
    "get_core_optimizer_info",
]
