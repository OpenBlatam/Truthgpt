"""
Compatibility Shims for Old Optimizer Files
============================================
Provides backward compatibility for code that imports old optimizer classes.
"""

import warnings
from typing import Dict, Any
import torch.nn as nn

from optimizers.base_truthgpt_optimizer import (
    UnifiedTruthGPTOptimizer,
    OptimizationLevel,
    OptimizationResult,
)


def _create_compat_optimizer(level: OptimizationLevel):
    """Create a compatibility optimizer wrapper."""
    class CompatOptimizer(UnifiedTruthGPTOptimizer):
        """Compatibility wrapper for old optimizer classes."""
        
        def __init__(self, config: Dict[str, Any] = None):
            warnings.warn(
                f"This optimizer class is deprecated. Use UnifiedTruthGPTOptimizer with level={level.value} instead.",
                DeprecationWarning,
                stacklevel=3
            )
            super().__init__(config=config, level=level)
    
    return CompatOptimizer


# Create compatibility classes for old optimizer names
AdvancedTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.ADVANCED)
ExpertTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.EXPERT)
UltimateTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.ULTIMATE)
SupremeTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.SUPREME)
EnterpriseTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.ENTERPRISE)
UltraFastTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.ULTRA_FAST)
UltraSpeedTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.ULTRA_SPEED)
HyperSpeedTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.HYPER_SPEED)
LightningSpeedTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.LIGHTNING_SPEED)
InfiniteTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.INFINITE)
TranscendentTruthGPTOptimizer = _create_compat_optimizer(OptimizationLevel.TRANSCENDENT)

# Export for backward compatibility
__all__ = [
    'AdvancedTruthGPTOptimizer',
    'ExpertTruthGPTOptimizer',
    'UltimateTruthGPTOptimizer',
    'SupremeTruthGPTOptimizer',
    'EnterpriseTruthGPTOptimizer',
    'UltraFastTruthGPTOptimizer',
    'UltraSpeedTruthGPTOptimizer',
    'HyperSpeedTruthGPTOptimizer',
    'LightningSpeedTruthGPTOptimizer',
    'InfiniteTruthGPTOptimizer',
    'TranscendentTruthGPTOptimizer',
]







