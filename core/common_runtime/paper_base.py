"""
Base Class for Research Paper Implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class PaperImplementationBase(ABC):
    """Abstract interface for paper implementation modules."""

    def __init__(self, paper_title: str, arxiv_id: str = ""):
        self.paper_title = paper_title
        self.arxiv_id = arxiv_id

    @abstractmethod
    def apply_technique(self, target: Any, **kwargs: Any) -> Any:
        """Apply paper optimization technique."""
        pass

    def get_metadata(self) -> Dict[str, str]:
        """Get paper metadata."""
        return {
            "title": self.paper_title,
            "arxiv_id": self.arxiv_id,
        }

