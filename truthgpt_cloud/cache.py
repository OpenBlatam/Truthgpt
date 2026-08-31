"""
⚡ TruthGPT Cloud - Semantic Proof & Inference Cache
Provides sub-millisecond retrieval for verified theorems, SMT proofs,
and frequent reasoning paths, reducing compute latency and token consumption.
"""

import hashlib
import json
import os
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Any, List, Tuple

logger = logging.getLogger("TruthGPT.CloudCache")


@dataclass
class CachedProofEntry:
    claim_hash: str
    claim_text: str
    certificate_data: Dict[str, Any]
    hit_count: int = 1
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    tokens_saved: int = 450


class CloudProofCache:
    """
    High-Performance Semantic Proof and KV Cache for TruthGPT Cloud.
    Caches Z3 SMT solver outputs, Merkle trees, and proof certificates.
    """

    def __init__(self, max_entries: int = 10000, storage_path: Optional[str] = None):
        self.max_entries = max_entries
        self.storage_path = storage_path
        self._proof_cache: Dict[str, CachedProofEntry] = {}
        self._total_hits: int = 0
        self._total_misses: int = 0
        self._total_tokens_saved: int = 0

    def _normalize_claim(self, claim: str, constraints: Optional[List[str]] = None) -> str:
        """Normalize mathematical claim string for deterministic hashing."""
        clean_claim = " ".join(claim.strip().lower().split())
        clean_constraints = " ".join(sorted([c.strip().lower() for c in (constraints or [])]))
        return f"{clean_claim}|{clean_constraints}"

    def compute_hash(self, claim: str, constraints: Optional[List[str]] = None) -> str:
        """Generate deterministic SHA-256 hash for a mathematical claim."""
        normalized = self._normalize_claim(claim, constraints)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_proof(self, claim: str, constraints: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached proof certificate if available."""
        h = self.compute_hash(claim, constraints)
        if h in self._proof_cache:
            entry = self._proof_cache[h]
            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._total_hits += 1
            self._total_tokens_saved += entry.tokens_saved
            logger.debug(f"Proof cache HIT for hash {h[:12]} (total hits: {self._total_hits})")
            return entry.certificate_data
        
        self._total_misses += 1
        return None

    def store_proof(
        self,
        claim: str,
        certificate_data: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        estimated_tokens: int = 450
    ) -> None:
        """Store a verified proof certificate in the semantic cache."""
        h = self.compute_hash(claim, constraints)
        
        # Evict oldest if capacity reached
        if len(self._proof_cache) >= self.max_entries:
            oldest_key = min(self._proof_cache.keys(), key=lambda k: self._proof_cache[k].last_accessed)
            del self._proof_cache[oldest_key]

        entry = CachedProofEntry(
            claim_hash=h,
            claim_text=claim,
            certificate_data=certificate_data,
            tokens_saved=estimated_tokens
        )
        self._proof_cache[h] = entry
        logger.debug(f"Stored proof in cache for hash {h[:12]}")

    def clear(self) -> None:
        """Flush the cache."""
        self._proof_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics and efficiency metrics."""
        total_requests = self._total_hits + self._total_misses
        hit_ratio = (self._total_hits / total_requests * 100.0) if total_requests > 0 else 0.0
        return {
            "cached_entries": len(self._proof_cache),
            "max_capacity": self.max_entries,
            "total_hits": self._total_hits,
            "total_misses": self._total_misses,
            "hit_ratio_percent": round(hit_ratio, 2),
            "total_tokens_saved": self._total_tokens_saved,
            "estimated_compute_ms_saved": round(self._total_hits * 14.5, 2)
        }


# Global Singleton Proof Cache
proof_cache = CloudProofCache()

__all__ = [
    "CachedProofEntry",
    "CloudProofCache",
    "proof_cache",
]
