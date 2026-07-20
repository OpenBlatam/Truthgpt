"""
Compatibility shim for hybrid_optimization_core.
DEPRECATED: Use UnifiedOptimizer with OptimizationLevel.EXPERT instead.
"""
import warnings
from typing import Dict, Any, Tuple
import torch.nn as nn

from .base_strategy import BaseOptimizationStrategy
from ...modules.optimizers.core.unified_optimizer import UnifiedOptimizer
from ...modules.optimizers.core.base_truthgpt_optimizer import OptimizationLevel, OptimizationResult

class HybridOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class HybridOptimizationCore(BaseOptimizationStrategy):
    """Backward-compatible facade around UnifiedOptimizer."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "HybridOptimizationCore is deprecated; "
            "use UnifiedOptimizer(level=OptimizationLevel.EXPERT).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        config_dict = self.config if isinstance(self.config, dict) else self.config.__dict__
        self._optimizer = UnifiedOptimizer(level=OptimizationLevel.EXPERT, config=config_dict)

    def optimize_module(self, module: nn.Module, context: Dict[str, Any] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """Legacy optimize_module API."""
        result = self._optimizer.optimize(module)
        return result.optimized_model, {
            "speed_improvement": result.speed_improvement,
            "memory_reduction": result.memory_reduction,
            "accuracy_preservation": result.accuracy_preservation,
            "optimization_time": result.optimization_time,
            "techniques_applied": result.techniques_applied,
        }

    def get_report(self) -> Dict[str, Any]:
        """Legacy get_report API."""
        if hasattr(self._optimizer, "get_report"):
            return self._optimizer.get_report()
        return {
            "message": "Report generated via UnifiedOptimizer shim",
            "optimizations_applied": len(getattr(self._optimizer, "_last_applied_techniques", [])),
        }

    def __getattr__(self, name):
        return getattr(self._optimizer, name)

def create_hybrid_optimization_core(config: Dict[str, Any] = None) -> HybridOptimizationCore:
    return HybridOptimizationCore(config)

__all__ = [
    "HybridOptimizationCore",
    "HybridOptimizationConfig",
    "create_hybrid_optimization_core",
]
