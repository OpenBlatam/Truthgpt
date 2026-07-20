"""
Compatibility shim for transcendent_optimization_core.

DEPRECATED: use ``UnifiedTruthGPTOptimizer`` with
``OptimizationLevel.TRANSCENDENT`` directly.
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

_LEVEL = OptimizationLevel.TRANSCENDENT


@dataclass
class TranscendentOptimizationConfig:
    """Legacy config — accepted for backward compatibility."""
    extra: Dict[str, Any] = field(default_factory=dict)


class TranscendentOptimizationCore:
    """Backward-compatible facade around UnifiedTruthGPTOptimizer(TRANSCENDENT)."""

    def __init__(self, config: Dict[str, Any] = None):
        warnings.warn(
            "TranscendentOptimizationCore is deprecated; "
            "use UnifiedTruthGPTOptimizer(level=OptimizationLevel.TRANSCENDENT).",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._optimizer = UnifiedTruthGPTOptimizer(config=self.config, level=_LEVEL)

    def optimize(self, model: nn.Module, **kwargs) -> OptimizationResult:
        return self._optimizer.optimize(model, **kwargs)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)


def create_transcendent_optimization_core(config: Dict[str, Any] = None) -> TranscendentOptimizationCore:
    return TranscendentOptimizationCore(config)


__all__ = [
    "TranscendentOptimizationCore",
    "TranscendentOptimizationConfig",
    "create_transcendent_optimization_core",
]
