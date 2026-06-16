"""
Unified Optimization Cores
==========================
Re-exports the legacy *_optimization_core public surface from the
backward-compatibility shims. New code should import
:class:`UnifiedTruthGPTOptimizer` from ``optimizers.core`` directly.
"""
from typing import Any, Dict, Optional

from ..compatibility.shims import (
    EnhancedOptimizationCore,
    EnhancedOptimizationConfig,
    create_enhanced_optimization_core,
    HybridOptimizationCore,
    HybridOptimizationConfig,
    create_hybrid_optimization_core,
    MegaEnhancedOptimizationCore,
    MegaEnhancedOptimizationConfig,
    create_mega_enhanced_optimization_core,
    SupremeOptimizationCore,
    SupremeOptimizationConfig,
    create_supreme_optimization_core,
    TranscendentOptimizationCore,
    TranscendentOptimizationConfig,
    create_transcendent_optimization_core,
    UltraEnhancedOptimizationCore,
    UltraEnhancedOptimizationConfig,
    create_ultra_enhanced_optimization_core,
    UltraFastOptimizationCore,
    UltraFastOptimizationConfig,
    create_ultra_fast_optimization_core,
)


_FACTORY_MAP = {
    "enhanced": create_enhanced_optimization_core,
    "ultra_enhanced": create_ultra_enhanced_optimization_core,
    "mega_enhanced": create_mega_enhanced_optimization_core,
    "supreme": create_supreme_optimization_core,
    "transcendent": create_transcendent_optimization_core,
    "hybrid": create_hybrid_optimization_core,
    "ultra_fast": create_ultra_fast_optimization_core,
}


def create_optimization_core(core_type: str = "enhanced", config: Optional[Dict[str, Any]] = None):
    """Unified factory function for any legacy optimization-core type."""
    key = core_type.lower()
    if key not in _FACTORY_MAP:
        raise ValueError(
            f"Unknown optimization core type: {core_type!r}. "
            f"Available types: {', '.join(_FACTORY_MAP)}"
        )
    return _FACTORY_MAP[key](config or {})


OPTIMIZATION_CORE_REGISTRY = {
    "enhanced":       {"class": EnhancedOptimizationCore,       "config": EnhancedOptimizationConfig,       "factory": create_enhanced_optimization_core},
    "ultra_enhanced": {"class": UltraEnhancedOptimizationCore,  "config": UltraEnhancedOptimizationConfig,  "factory": create_ultra_enhanced_optimization_core},
    "mega_enhanced":  {"class": MegaEnhancedOptimizationCore,   "config": MegaEnhancedOptimizationConfig,   "factory": create_mega_enhanced_optimization_core},
    "supreme":        {"class": SupremeOptimizationCore,        "config": SupremeOptimizationConfig,        "factory": create_supreme_optimization_core},
    "transcendent":   {"class": TranscendentOptimizationCore,   "config": TranscendentOptimizationConfig,   "factory": create_transcendent_optimization_core},
    "hybrid":         {"class": HybridOptimizationCore,         "config": HybridOptimizationConfig,         "factory": create_hybrid_optimization_core},
    "ultra_fast":     {"class": UltraFastOptimizationCore,      "config": UltraFastOptimizationConfig,      "factory": create_ultra_fast_optimization_core},
}


def list_available_cores() -> list:
    return list(OPTIMIZATION_CORE_REGISTRY)


def get_core_info(core_type: str) -> Dict[str, Any]:
    if core_type not in OPTIMIZATION_CORE_REGISTRY:
        raise ValueError(f"Unknown core type: {core_type}")
    entry = OPTIMIZATION_CORE_REGISTRY[core_type]
    return {
        "type": core_type,
        "class": entry["class"].__name__,
        "config_class": entry["config"].__name__,
        "factory": entry["factory"].__name__,
    }


__all__ = [
    "EnhancedOptimizationCore",
    "UltraEnhancedOptimizationCore",
    "MegaEnhancedOptimizationCore",
    "SupremeOptimizationCore",
    "TranscendentOptimizationCore",
    "HybridOptimizationCore",
    "UltraFastOptimizationCore",
    "EnhancedOptimizationConfig",
    "UltraEnhancedOptimizationConfig",
    "MegaEnhancedOptimizationConfig",
    "SupremeOptimizationConfig",
    "TranscendentOptimizationConfig",
    "HybridOptimizationConfig",
    "UltraFastOptimizationConfig",
    "create_enhanced_optimization_core",
    "create_ultra_enhanced_optimization_core",
    "create_mega_enhanced_optimization_core",
    "create_supreme_optimization_core",
    "create_transcendent_optimization_core",
    "create_hybrid_optimization_core",
    "create_ultra_fast_optimization_core",
    "create_optimization_core",
    "OPTIMIZATION_CORE_REGISTRY",
    "list_available_cores",
    "get_core_info",
]
