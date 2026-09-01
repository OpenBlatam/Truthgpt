"""
⚡ TruthGPT Cloud - Cache Compatibility Bridge
Re-exports semantic proof cache and entry structures from canonical truthgpt_cloud.cache subpackage.
"""

from .cache import (
    BaseProofCache,
    CachedProofEntry,
    CloudProofCache,
    proof_cache,
)

__all__ = [
    "BaseProofCache",
    "CachedProofEntry",
    "CloudProofCache",
    "proof_cache",
]
