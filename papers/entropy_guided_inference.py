"""
Entropy-Guided Adaptive Inference Module
========================================
Based on "From Rigid to Dynamic: Entropy-Guided Adaptive Inference for Long-Context LLMs"
(arXiv:2606.09508v1, June 2026)

Key idea (EntropyInfer):
------------------------
Attention entropy varies across heads and segments of a long prompt.
Low-entropy segments computed with sparse attention slash compute while
high-entropy segments keep full attention, enabling up to ~2.39x speedup training-free.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import EntropyGuidedConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class EntropyGuidedInference(BasePaperModule):
    """
    Simulates entropy-guided adaptive compute allocation during prefill.
    """

    metadata = PaperMetadata(
        paper_id="entropy_guided_inference",
        paper_name="From Rigid to Dynamic: Entropy-Guided Adaptive Inference for Long-Context LLMs",
        category=PaperCategory.INFERENCE_EFFICIENCY,
        arxiv_id="2606.09508v1",
        year=2026,
        authors=["EntropyInfer Authors"],
        key_techniques=["Attention Entropy Proxy", "Sparse Attention Routing", "Training-Free"],
        speedup=2.39,
        description="Selects sparse vs full attention adaptively using attention entropy.",
        scholar_query="Entropy-Guided Adaptive Inference Long-Context LLMs",
    )

    def __init__(
        self,
        entropy_threshold: float = 0.55,
        sparse_cost_ratio: float = 0.25,
        max_speedup: float = 2.39,
        config: Optional[EntropyGuidedConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = EntropyGuidedConfig(
                entropy_threshold=entropy_threshold,
                sparse_cost_ratio=sparse_cost_ratio,
                max_speedup=max_speedup,
            )
            self.config.validate()

        self.entropy_threshold = self.config.entropy_threshold
        self.sparse_cost_ratio = self.config.sparse_cost_ratio
        self.max_speedup = self.config.max_speedup

    def estimate_segment_entropy(self, num_segments: int) -> List[float]:
        """Estimate a normalized [0, 1] attention-entropy proxy per context segment."""
        if num_segments <= 0:
            return []

        entropies: List[float] = []
        for i in range(num_segments):
            position = i / max(num_segments - 1, 1)
            boundary = 1.0 - abs(position - 0.5) * 2.0
            focused = 0.5 + 0.45 * abs(math.cos(i * 0.7))
            entropies.append(round(max(0.0, min(1.0, focused - 0.3 * boundary)), 4))
        return entropies

    def allocate_compute(self, context_length: int, segment_size: int = 1024) -> PaperResult:
        """
        Decide per-segment attention density and report projected speedup.
        """
        if context_length < 0:
            raise PaperValidationError(f"context_length cannot be negative, got {context_length}")
        if segment_size <= 0:
            raise PaperValidationError(f"segment_size must be positive, got {segment_size}")

        if context_length == 0:
            return PaperResult({
                "context_length": 0,
                "num_segments": 0,
                "full_attention_segments": 0,
                "sparse_attention_segments": 0,
                "compute_fraction": 1.0,
                "speedup_multiplier": 1.0,
                "training_free": True,
            })

        num_segments = max(1, math.ceil(context_length / segment_size))
        entropies = self.estimate_segment_entropy(num_segments)

        full_segments = [i for i, e in enumerate(entropies) if e >= self.entropy_threshold]
        sparse_segments = [i for i, e in enumerate(entropies) if e < self.entropy_threshold]

        adaptive_cost = len(full_segments) + len(sparse_segments) * self.sparse_cost_ratio
        dense_cost = float(num_segments)
        raw_speedup = dense_cost / adaptive_cost if adaptive_cost > 0 else 1.0
        speedup = min(raw_speedup, self.max_speedup)

        return PaperResult({
            "context_length": context_length,
            "num_segments": num_segments,
            "full_attention_segments": len(full_segments),
            "sparse_attention_segments": len(sparse_segments),
            "compute_fraction": round(adaptive_cost / dense_cost, 4) if dense_cost > 0 else 1.0,
            "speedup_multiplier": round(speedup, 4),
            "training_free": True,
        })

    def execute(self, context_length: int = 8192, segment_size: int = 1024, **kwargs: Any) -> PaperResult:
        """Execute entropy guided compute allocation."""
        ctx_len = kwargs.get("context_length", context_length)
        seg_sz = kwargs.get("segment_size", segment_size)
        return self.allocate_compute(ctx_len, segment_size=seg_sz)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "entropy_threshold": self.entropy_threshold,
            "sparse_cost_ratio": self.sparse_cost_ratio,
            "max_speedup": self.max_speedup,
        }


__all__ = ["EntropyGuidedInference"]
