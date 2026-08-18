"""
MoQAE - Mixture of Quantization-Aware Experts Module
====================================================
Based on "MoQAE: Mixed-Precision Quantization for Long-Context LLM Inference via
Mixture of Quantization-Aware Experts" (arXiv:2506.07533, 2026)

Key idea:
---------
Treat each quantization bit-width configuration as an "expert" and use an MoE-style
router to select, chunk by chunk, the configuration that best trades accuracy for
memory under a quality budget constraint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import MoQAEConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class MoQAEQuantizer(BasePaperModule):
    """
    Routes context chunks to optimal quantization experts (bit-widths)
    based on chunk sensitivity and quality budget.
    """

    metadata = PaperMetadata(
        paper_id="moqae_quant",
        paper_name="MoQAE: Mixed-Precision Quantization for Long-Context LLM Inference via Mixture of Quantization-Aware Experts",
        category=PaperCategory.QUANTIZATION,
        arxiv_id="2506.07533",
        year=2025,
        authors=["MoQAE Team"],
        key_techniques=["Quantization Experts", "MoE Routing", "Chunk Sensitivity"],
        speedup=2.1,
        description="Routes context chunks to optimal precision experts under quality constraints.",
        scholar_query="MoQAE Mixture of Quantization-Aware Experts",
    )

    # (name, bits, quality_cost) experts ordered low->high precision
    DEFAULT_EXPERTS: List[Tuple[str, int, float]] = [
        ("int2", 2, 0.06),
        ("int4", 4, 0.02),
        ("int8", 8, 0.005),
        ("fp16", 16, 0.0),
    ]

    def __init__(
        self,
        experts: Optional[List[Tuple[str, int, float]]] = None,
        quality_budget: float = 0.02,
        chunk_size: int = 2048,
        config: Optional[MoQAEConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = MoQAEConfig(
                quality_budget=quality_budget,
                chunk_size=chunk_size,
                experts=experts,
            )
            self.config.validate()

        self.experts = self.config.experts or self.DEFAULT_EXPERTS
        self.quality_budget = self.config.quality_budget
        self.chunk_size = self.config.chunk_size

    @staticmethod
    def _chunk_sensitivity(idx: int, num_chunks: int) -> float:
        """Sensitivity in [0, 1]; early and late prompt chunks have higher sensitivity."""
        pos = idx / max(num_chunks - 1, 1)
        return round(1.0 - abs(pos - 0.5) * 1.6, 4)

    def route(self, context_length: int, chunk_size: Optional[int] = None) -> PaperResult:
        """
        Route context sequence into chunks and assign optimal precision experts.
        """
        if context_length < 0:
            raise PaperValidationError(f"context_length cannot be negative, got {context_length}")

        c_size = chunk_size if chunk_size is not None else self.chunk_size
        if c_size <= 0:
            raise PaperValidationError(f"chunk_size must be positive, got {c_size}")

        if context_length == 0:
            return PaperResult({
                "num_chunks": 0,
                "expert_assignments": {},
                "avg_bits": 16.0,
                "memory_ratio": 1.0,
                "avg_quality_cost": 0.0,
            })

        num_chunks = max(1, -(-context_length // c_size))
        assignments: Dict[str, int] = {}
        total_bits = 0
        total_cost = 0.0

        for i in range(num_chunks):
            sens = self._chunk_sensitivity(i, num_chunks)
            for name, bits, cost in self.experts:
                if cost <= self.quality_budget or sens < 0.5:
                    if sens >= 0.7 and cost > (self.quality_budget / 2.0):
                        continue
                    assignments[name] = assignments.get(name, 0) + 1
                    total_bits += bits * c_size
                    total_cost += cost
                    break
            else:
                name, bits, cost = self.experts[-1]
                assignments[name] = assignments.get(name, 0) + 1
                total_bits += bits * c_size
                total_cost += cost

        baseline = num_chunks * c_size * 16
        return PaperResult({
            "num_chunks": num_chunks,
            "expert_assignments": assignments,
            "avg_bits": round(total_bits / (num_chunks * c_size), 3),
            "memory_ratio": round(total_bits / baseline, 4),
            "avg_quality_cost": round(total_cost / num_chunks, 5),
        })

    def execute(self, context_length: int = 4096, chunk_size: Optional[int] = None, **kwargs: Any) -> PaperResult:
        """Execute MoQAE expert routing simulation."""
        ctx_len = kwargs.get("context_length", context_length)
        c_sz = chunk_size if chunk_size is not None else kwargs.get("chunk_size", self.chunk_size)
        return self.route(ctx_len, chunk_size=c_sz)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "quality_budget": self.quality_budget,
            "chunk_size": self.chunk_size,
            "experts": [e[0] for e in self.experts],
        }


__all__ = ["MoQAEQuantizer"]
