"""
Compatibility shim for enhanced_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.ADVANCED`` directly.
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

_LEVEL = OptimizationLevel.ADVANCED


@dataclass
class EnhancedOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    optimization_aggressiveness: float = 0.8
    memory_efficiency_threshold: float = 0.9
    computational_efficiency_threshold: float = 0.85
    extra: Dict[str, Any] = field(default_factory=dict)


class EnhancedOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(ADVANCED)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "EnhancedOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.ADVANCED).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_enhanced_optimization_core(config: Dict[str, Any] = None) -> EnhancedOptimizationCore:
    return EnhancedOptimizationCore(config)


__all__ = [
    "EnhancedOptimizationCore",
    "EnhancedOptimizationConfig",
    "create_enhanced_optimization_core",
]
