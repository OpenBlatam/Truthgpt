"""
⚡ TruthGPT Cloud - Proof & Semantic Cache Subpackage
Exports cache interfaces, entries, and the singleton proof cache.
"""

from .base import BaseProofCache
from .proof_cache import (
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
