"""
PTE - Progressive Thought Encoding
==================================
Based on "Training Large Reasoning Models Efficiently via Progressive Thought
Encoding" (arXiv:2602.16839, Feb 2026)

Key idea:
---------
Long chain-of-thought traces are expensive to train on. PTE applies a curriculum
that progressively encodes verbose thoughts into denser representations across training stages.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import ProgressiveThoughtConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class ProgressiveThoughtEncoder(BasePaperModule):
    """
    Simulates the progressive compression curriculum over training stages.
    """

    metadata = PaperMetadata(
        paper_id="progressive_thought_encoding",
        paper_name="Training Large Reasoning Models Efficiently via Progressive Thought Encoding",
        category=PaperCategory.REASONING,
        arxiv_id="2602.16839",
        year=2026,
        authors=["PTE Authors"],
        key_techniques=["Progressive Thought Compression", "Curriculum Training", "Token Annealing"],
        speedup=1.7,
        description="Progressively compresses verbose chain-of-thought traces during training.",
        scholar_query="Training Large Reasoning Models Efficiently Progressive Thought Encoding",
    )

    def __init__(
        self,
        num_stages: int = 4,
        final_compression: float = 0.3,
        config: Optional[ProgressiveThoughtConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = ProgressiveThoughtConfig(
                num_stages=num_stages,
                final_compression=final_compression,
            )
            self.config.validate()

        self.num_stages = max(1, self.config.num_stages)
        self.final_compression = max(0.05, min(1.0, self.config.final_compression))

    def curriculum(self, base_thought_tokens: int = 1000) -> PaperResult:
        """
        Returns the per-stage thought-token budget and total training-token savings.
        """
        if base_thought_tokens < 1:
            base_thought_tokens = 1

        stages: List[Dict[str, Any]] = []
        for s in range(self.num_stages):
            frac = 1.0 - (1.0 - self.final_compression) * (s / max(self.num_stages - 1, 1))
            tokens = max(1, int(round(base_thought_tokens * frac)))
            stages.append({"stage": s, "keep_fraction": round(frac, 4), "thought_tokens": tokens})

        used = sum(st["thought_tokens"] for st in stages)
        full = base_thought_tokens * self.num_stages
        savings = (full - used) / full if full > 0 else 0.0

        return PaperResult({
            "base_thought_tokens": base_thought_tokens,
            "num_stages": self.num_stages,
            "stages": stages,
            "final_thought_tokens": stages[-1]["thought_tokens"],
            "training_token_savings_pct": round(savings * 100, 2),
        })

    def get_stage_budget(self, current_step: int, total_steps: int, base_tokens: int) -> int:
        """Compute continuous thought token budget for a given training step."""
        if total_steps <= 0:
            return base_tokens
        progress = min(max(float(current_step) / total_steps, 0.0), 1.0)
        frac = 1.0 - (1.0 - self.final_compression) * progress
        return max(1, int(round(base_tokens * frac)))

    def execute(self, base_thought_tokens: int = 1000, **kwargs: Any) -> PaperResult:
        """Execute progressive thought encoding curriculum calculation."""
        tokens = kwargs.get("base_thought_tokens", base_thought_tokens)
        return self.curriculum(tokens)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "num_stages": self.num_stages,
            "final_compression": self.final_compression,
        }


__all__ = ["ProgressiveThoughtEncoder"]
