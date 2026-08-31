"""
💎 TruthGPT Cloud - Tiers Compatibility Bridge
Re-exports tier structures from the canonical truthgpt_cloud.core.tiers package.
"""

from .core.tiers import (
    CloudTier,
    TierConfig,
    TIER_CONFIGURATIONS,
    get_tier_config,
    get_all_tiers
)

__all__ = [
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
]
