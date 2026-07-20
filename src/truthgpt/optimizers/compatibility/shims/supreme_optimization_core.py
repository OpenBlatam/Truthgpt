"""
Compatibility shim for supreme_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.SUPREME`` directly.
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

_LEVEL = OptimizationLevel.SUPREME


@dataclass
class SupremeOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class SupremeOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(SUPREME)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "SupremeOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.SUPREME).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_supreme_optimization_core(config: Dict[str, Any] = None) -> SupremeOptimizationCore:
    return SupremeOptimizationCore(config)


__all__ = [
    "SupremeOptimizationCore",
    "SupremeOptimizationConfig",
    "create_supreme_optimization_core",
]
