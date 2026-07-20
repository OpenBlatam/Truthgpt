"""
Compatibility shim for hybrid_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.EXPERT`` directly.
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

_LEVEL = OptimizationLevel.EXPERT


@dataclass
class HybridOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class HybridOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(EXPERT)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "HybridOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.EXPERT).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_hybrid_optimization_core(config: Dict[str, Any] = None) -> HybridOptimizationCore:
    return HybridOptimizationCore(config)


__all__ = [
    "HybridOptimizationCore",
    "HybridOptimizationConfig",
    "create_hybrid_optimization_core",
]
