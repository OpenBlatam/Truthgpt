"""
⚡ TruthGPT Cloud - Semantic Cache Data Models
"""

import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

from ..core.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS,
)


@dataclass
class CachedProofEntry:
    claim_hash: str
    claim_text: str
    certificate_data: Dict[str, Any]
    hit_count: int = 1
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    tokens_saved: int = DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS
    ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS
    embedding: Optional[List[float]] = None

    @property
    def is_expired(self) -> bool:
        """Check if this entry has exceeded its TTL."""
        if self.ttl_seconds <= 0:
            return False  # TTL of 0 means no expiration
        return (time.time() - self.created_at) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["is_expired"] = self.is_expired
        return d


__all__ = ["CachedProofEntry"]
