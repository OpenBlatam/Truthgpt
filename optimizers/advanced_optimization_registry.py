"""
Advanced optimization registry for managing enhanced optimization techniques.
Unified interface re-exporting and wrapping advanced_optimization_registry_v2.
"""

import warnings
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn

from .advanced_optimization_registry_v2 import (
    AdvancedOptimizationConfig,
    ADVANCED_OPTIMIZATION_CONFIGS,
    get_advanced_optimization_config as get_v2_config,
    apply_advanced_optimizations as apply_v2_optimizations,
    get_advanced_optimization_report as get_v2_report,
)

OPTIMIZATION_CONFIGS = ADVANCED_OPTIMIZATION_CONFIGS


def get_advanced_optimization_config(variant_name: str) -> AdvancedOptimizationConfig:
    """Get advanced optimization configuration for a specific variant."""
    return get_v2_config(variant_name)


def apply_advanced_optimizations(model: nn.Module, config: AdvancedOptimizationConfig) -> nn.Module:
    """Apply advanced optimizations to a model using the unified engine."""
    return apply_v2_optimizations(model, config)


def get_advanced_optimization_report(model: nn.Module) -> Dict[str, Any]:
    """Get comprehensive advanced optimization report from unified registry."""
    return get_v2_report(model)


__all__ = [
    "AdvancedOptimizationConfig",
    "OPTIMIZATION_CONFIGS",
    "get_advanced_optimization_config",
    "apply_advanced_optimizations",
    "get_advanced_optimization_report",
]

