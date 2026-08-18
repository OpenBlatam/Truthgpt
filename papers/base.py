"""
Base definitions, enums, metadata, structured result objects, and abstract classes
for the TruthGPT Research Papers Subsystem.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class PaperCategory(str, Enum):
    """
    Unified categorization of research papers according to system optimization area.
    Supports both legacy and extended category keys.
    """
    KV_CACHE = "kv_cache"
    REASONING = "reasoning"
    QUANTIZATION = "quantization"
    RL_ALIGNMENT = "rl_alignment"
    RL_OPTIMIZATION = "rl_optimization"
    INFERENCE_EFFICIENCY = "inference_efficiency"
    INFERENCE = "inference"
    MULTI_AGENT = "multi_agent"
    MULTI_AGENT_MEMORY = "multi_agent_memory"
    TRAINING_STABILITY = "training_stability"
    STABILITY = "stability"

    @classmethod
    def from_str(cls, val: Union[str, PaperCategory]) -> PaperCategory:
        """Parse string or enum into PaperCategory safely."""
        if isinstance(val, PaperCategory):
            return val
        val_str = str(val).lower().strip()
        mapping = {
            "kv_cache": cls.KV_CACHE,
            "reasoning": cls.REASONING,
            "quantization": cls.QUANTIZATION,
            "rl_alignment": cls.RL_ALIGNMENT,
            "rl_optimization": cls.RL_OPTIMIZATION,
            "inference_efficiency": cls.INFERENCE_EFFICIENCY,
            "inference": cls.INFERENCE,
            "multi_agent": cls.MULTI_AGENT,
            "multi_agent_memory": cls.MULTI_AGENT_MEMORY,
            "training_stability": cls.TRAINING_STABILITY,
            "stability": cls.STABILITY,
        }
        return mapping.get(val_str, cls.INFERENCE)


@dataclass
class PaperMetadata:
    """
    Structured metadata representing a published research paper and its specifications.
    """
    paper_id: str
    paper_name: str
    category: PaperCategory = PaperCategory.INFERENCE
    arxiv_id: Optional[str] = None
    year: int = 2026
    authors: List[str] = field(default_factory=list)
    key_techniques: List[str] = field(default_factory=list)
    speedup: Optional[float] = None
    accuracy_improvement: Optional[float] = None
    description: str = ""
    scholar_query: str = ""
    url: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.category, PaperCategory):
            self.category = PaperCategory.from_str(self.category)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a serializable dictionary representation."""
        data = asdict(self)
        data["category"] = self.category.value if isinstance(self.category, PaperCategory) else str(self.category)
        return data


class PaperResult(dict):
    """
    Structured dictionary-like result object returned by paper implementation modules.
    Supports both attribute access (res.speedup) and dictionary access (res['speedup'])
    with recursive wrapping of nested structures for complete interoperability.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        initial: Dict[str, Any] = {}
        if args:
            if len(args) == 1 and isinstance(args[0], (dict, list)):
                if isinstance(args[0], dict):
                    initial.update(args[0])
            else:
                initial.update(dict(*args))
        initial.update(kwargs)

        for k, v in initial.items():
            self[k] = v

    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: Any) -> None:
        wrapped = self._wrap(value)
        super().__setitem__(key, wrapped)
        self.__dict__[key] = wrapped

    def __getattr__(self, key: str) -> Any:
        if key in self:
            return self[key]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute or key '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __delattr__(self, key: str) -> None:
        if key in self:
            del self[key]
        if key in self.__dict__:
            del self.__dict__[key]

    def __repr__(self) -> str:
        return f"PaperResult({dict(self)})"

    @classmethod
    def _wrap(cls, value: Any) -> Any:
        """Recursively wrap dictionaries and lists in PaperResult instances."""
        if isinstance(value, dict) and not isinstance(value, PaperResult):
            return PaperResult(value)
        if isinstance(value, list):
            return [cls._wrap(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._wrap(item) for item in value)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Safe dict lookup with default."""
        return super().get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert recursively to standard python dict."""
        result: Dict[str, Any] = {}
        for k, v in self.items():
            if isinstance(v, PaperResult):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if isinstance(item, PaperResult) else item for item in v]
            elif isinstance(v, tuple):
                result[k] = tuple(item.to_dict() if isinstance(item, PaperResult) else item for item in v)
            else:
                result[k] = v
        return result


class BasePaperModule(ABC):
    """
    Abstract base class for all research paper implementation modules.
    Enforces standardized metadata access, execution, parameter validation,
    and automated benchmarking facilities.
    """

    metadata: PaperMetadata

    def __init__(self, **kwargs: Any) -> None:
        self.logger = logging.getLogger(self.__class__.__module__)

    @classmethod
    def get_metadata(cls) -> PaperMetadata:
        """Returns the paper metadata associated with this module."""
        if hasattr(cls, "metadata") and isinstance(cls.metadata, PaperMetadata):
            return cls.metadata
        return PaperMetadata(
            paper_id=cls.__name__.lower(),
            paper_name=cls.__name__,
            category=PaperCategory.INFERENCE,
            description=cls.__doc__ or "",
        )

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> PaperResult:
        """Standard execution entrypoint for running the paper algorithm."""
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary and parameters of the algorithm."""
        return {
            "algorithm": self.__class__.__name__,
            "metadata": self.get_metadata().to_dict(),
        }

    def benchmark(self, num_runs: int = 10, **kwargs: Any) -> PaperResult:
        """
        Run execution multiple times to benchmark latency, throughput, and output.
        """
        latencies: List[float] = []
        last_result: Optional[PaperResult] = None

        runs = max(1, num_runs)
        for _ in range(runs):
            t0 = time.perf_counter()
            last_result = self.execute(**kwargs)
            latencies.append(time.perf_counter() - t0)

        avg_latency_ms = (sum(latencies) / len(latencies)) * 1000.0
        min_latency_ms = min(latencies) * 1000.0
        max_latency_ms = max(latencies) * 1000.0

        meta = self.get_metadata()
        return PaperResult({
            "paper_id": meta.paper_id,
            "paper_name": meta.paper_name,
            "category": meta.category.value if isinstance(meta.category, PaperCategory) else str(meta.category),
            "num_runs": len(latencies),
            "avg_latency_ms": round(avg_latency_ms, 4),
            "min_latency_ms": round(min_latency_ms, 4),
            "max_latency_ms": round(max_latency_ms, 4),
            "last_result": last_result.to_dict() if last_result else {},
        })

    def reset(self) -> None:
        """Reset internal mutable state if applicable."""
        pass


__all__ = [
    "PaperCategory",
    "PaperMetadata",
    "PaperResult",
    "BasePaperModule",
]
