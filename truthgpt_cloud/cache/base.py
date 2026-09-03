"""
⚡ TruthGPT Cloud - Cache Abstract Base Interface
Defines the contract for semantic proof, KV, and theorem caching systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseProofCache(ABC):
    """Abstract base class for proof and theorem caching backends."""

    @abstractmethod
    def get_proof(self, claim: str, constraints: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached proof certificate data for a claim."""
        pass

    @abstractmethod
    def store_proof(
        self,
        claim: str,
        certificate_data: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        estimated_tokens: int = 450
    ) -> None:
        """Store a verified proof certificate in the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Flush the cache."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return cache hit/miss and efficiency metrics."""
        pass

    def __len__(self) -> int:
        """Return the number of entries currently in the cache."""
        return 0


__all__ = ["BaseProofCache"]
