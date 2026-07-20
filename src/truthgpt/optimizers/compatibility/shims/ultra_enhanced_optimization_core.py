"""
Compatibility shim for ultra_enhanced_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.ENTERPRISE`` directly.
"""
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict

import torch.nn as nn

from ...core.base_truthgpt_optimizer import (
    OptimizationLevel,
    OptimizationResult,
    UnifiedTruthGPTOptimizer,
)

_LEVEL = OptimizationLevel.ENTERPRISE


@dataclass
class UltraEnhancedOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class UltraEnhancedOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(ENTERPRISE)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "UltraEnhancedOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.ENTERPRISE).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_ultra_enhanced_optimization_core(config: Dict[str, Any] = None) -> UltraEnhancedOptimizationCore:
    return UltraEnhancedOptimizationCore(config)


__all__ = [
    "UltraEnhancedOptimizationCore",
    "UltraEnhancedOptimizationConfig",
    "create_ultra_enhanced_optimization_core",
]
