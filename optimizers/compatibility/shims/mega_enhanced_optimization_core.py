"""
Compatibility shim for mega_enhanced_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.MASTER`` directly.
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

_LEVEL = OptimizationLevel.MASTER


@dataclass
class MegaEnhancedOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class MegaEnhancedOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(MASTER)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "MegaEnhancedOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.MASTER).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_mega_enhanced_optimization_core(config: Dict[str, Any] = None) -> MegaEnhancedOptimizationCore:
    return MegaEnhancedOptimizationCore(config)


__all__ = [
    "MegaEnhancedOptimizationCore",
    "MegaEnhancedOptimizationConfig",
    "create_mega_enhanced_optimization_core",
]
