"""
📚 TruthGPT Cloud - Paper Data Models
Defines research paper representations, metadata, and citation structures.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class PaperItem:
    paper_id: str
    title: str
    authors: List[str]
    published: str
    impact_factor: float
    category: str
    abstract: str
    cloud_status: str
    supported_tiers: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize paper item into dictionary format."""
        return asdict(self)


__all__ = [
    "PaperItem",
]
