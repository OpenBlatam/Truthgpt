"""
Interfaces and Abstract Base Classes for TruthGPT research paper implementations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type


class PaperCategory(str, Enum):
    """Categorization of research papers according to system optimization area."""
    KV_CACHE = "kv_cache"
    REASONING = "reasoning"
    QUANTIZATION = "quantization"
    RL_ALIGNMENT = "rl_alignment"
    RL_OPTIMIZATION = "rl_alignment"
    INFERENCE_EFFICIENCY = "inference_efficiency"
    INFERENCE = "inference_efficiency"
    MULTI_AGENT = "multi_agent"
    MULTI_AGENT_MEMORY = "multi_agent"
    TRAINING_STABILITY = "training_stability"
    STABILITY = "training_stability"


@dataclass(frozen=True)
class PaperMetadata:
    """
    Structured metadata representing a published research paper.
    """
    paper_id: str
    paper_name: str
    category: PaperCategory
    arxiv_id: Optional[str] = None
    year: int = 2026
    authors: List[str] = field(default_factory=list)
    key_techniques: List[str] = field(default_factory=list)
    speedup: Optional[float] = None
    accuracy_improvement: Optional[float] = None
    description: str = ""
    scholar_query: str = ""
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary representation."""
        cat_val = self.category.value if isinstance(self.category, PaperCategory) else str(self.category)
        return {
            "paper_id": self.paper_id,
            "paper_name": self.paper_name,
            "category": cat_val,
            "arxiv_id": self.arxiv_id,
            "year": self.year,
            "authors": self.authors,
            "key_techniques": self.key_techniques,
            "speedup": self.speedup,
            "accuracy_improvement": self.accuracy_improvement,
            "description": self.description,
            "scholar_query": self.scholar_query,
            "url": self.url or (f"https://arxiv.org/abs/{self.arxiv_id}" if self.arxiv_id else None),
        }


class PaperResult(dict):
    """
    Structured dictionary-like result object returned by paper modules.
    Supports both attribute access (.speedup) and dictionary access (['speedup'])
    for complete backward compatibility.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            if isinstance(args[0], dict):
                super().__init__(args[0])
                for k, v in args[0].items():
                    self.__dict__[k] = v
            else:
                super().__init__(*args, **kwargs)
        else:
            super().__init__(**kwargs)
        for key, value in kwargs.items():
            self.__dict__[key] = value

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        self.__dict__[key] = value

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value
        self.__dict__[key] = value

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'PaperResult' object has no attribute '{key}'")

    def to_dict(self) -> Dict[str, Any]:
        """Return a pure python dict representation."""
        result: Dict[str, Any] = {}
        for k, v in self.items():
            if isinstance(v, PaperResult):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if isinstance(item, PaperResult) else item for item in v]
            else:
                result[k] = v
        return result


class BasePaperAlgorithm(ABC):
    """
    Abstract base class for all research paper algorithm implementations.
    """
    metadata: Optional[PaperMetadata] = None

    def __init__(self, **kwargs: Any) -> None:
        self.logger = logging.getLogger(self.__class__.__module__)

    @classmethod
    def get_metadata(cls) -> Optional[PaperMetadata]:
        """Return metadata associated with the paper implementation."""
        return cls.metadata

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary and parameters of the algorithm."""
        meta = self.get_metadata()
        return {
            "paper_id": meta.paper_id if meta else self.__class__.__name__.lower(),
            "paper_name": meta.paper_name if meta else self.__class__.__name__,
            "class_name": self.__class__.__name__,
        }

    def execute(self, *args: Any, **kwargs: Any) -> PaperResult:
        """Standard execution method for running the paper algorithm."""
        summary = self.get_summary()
        return PaperResult(summary)

    def benchmark(self, num_runs: int = 10, **kwargs: Any) -> Dict[str, Any]:
        """Benchmark latency of execution."""
        import time
        latencies: List[float] = []
        last_result: Optional[Any] = None
        for _ in range(max(1, num_runs)):
            t0 = time.perf_counter()
            last_result = self.execute(**kwargs)
            latencies.append(time.perf_counter() - t0)

        meta = self.get_metadata()
        return {
            "paper_id": meta.paper_id if meta else self.__class__.__name__.lower(),
            "paper_name": meta.paper_name if meta else self.__class__.__name__,
            "num_runs": len(latencies),
            "avg_latency_ms": round((sum(latencies) / len(latencies)) * 1000.0, 4),
            "min_latency_ms": round(min(latencies) * 1000.0, 4),
            "max_latency_ms": round(max(latencies) * 1000.0, 4),
            "last_result": last_result.to_dict() if hasattr(last_result, "to_dict") else last_result,
        }

    def reset(self) -> None:
        """Reset internal mutable state."""
        pass


BasePaperModule = BasePaperAlgorithm


class PaperRegistryInterface(ABC):
    """
    Interface defining registry operations for discovery and lookup of papers.
    """
    @abstractmethod
    def list_papers(self, category: Optional[str] = None) -> List[PaperMetadata]:
        """List paper metadata matching optional category."""
        pass

    @abstractmethod
    def get_paper(self, paper_id: str) -> Optional[PaperMetadata]:
        """Retrieve paper metadata by paper identifier."""
        pass

    @abstractmethod
    def create_algorithm(self, paper_id: str, **kwargs: Any) -> BasePaperAlgorithm:
        """Instantiate algorithm implementation associated with paper ID."""
        pass


__all__ = [
    "PaperCategory",
    "PaperMetadata",
    "PaperResult",
    "BasePaperAlgorithm",
    "BasePaperModule",
    "PaperRegistryInterface",
]
