"""
Compatibility shim for ultra_fast_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.ULTRA_FAST`` directly.
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

_LEVEL = OptimizationLevel.ULTRA_FAST


@dataclass
class UltraFastOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class UltraFastOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(ULTRA_FAST)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "UltraFastOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.ULTRA_FAST).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_ultra_fast_optimization_core(config: Dict[str, Any] = None) -> UltraFastOptimizationCore:
    return UltraFastOptimizationCore(config)


__all__ = [
    "UltraFastOptimizationCore",
    "UltraFastOptimizationConfig",
    "create_ultra_fast_optimization_core",
]
