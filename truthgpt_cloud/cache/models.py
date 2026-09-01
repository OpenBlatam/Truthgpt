"""
⚡ TruthGPT Cloud - Semantic Cache Data Models
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class CachedProofEntry:
    claim_hash: str
    claim_text: str
    certificate_data: Dict[str, Any]
    hit_count: int = 1
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    tokens_saved: int = 450


__all__ = ["CachedProofEntry"]
