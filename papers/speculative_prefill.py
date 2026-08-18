"""
Cross-Family Speculative Prefill Module
=======================================
Based on "Cross-Family Speculative Prefill: Training-Free Long-Context
Compression with Small Draft Models" (arXiv:2603.02631, 2026)

Key idea:
---------
Use a small draft model at inference time to estimate token-level importance over a
long prompt, then prefill only the most important tokens into the large model.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import SpeculativePrefillConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class SpeculativePrefillCompressor(BasePaperModule):
    """
    Simulates draft-model-guided prefill compression: keep top tokens, drop the rest.
    """

    metadata = PaperMetadata(
        paper_id="speculative_prefill",
        paper_name="Cross-Family Speculative Prefill: Training-Free Long-Context Compression with Small Draft Models",
        category=PaperCategory.INFERENCE_EFFICIENCY,
        arxiv_id="2603.02631",
        year=2026,
        authors=["Speculative Prefill Team"],
        key_techniques=["Cross-Family Drafting", "Training-Free Compression", "Token Importance Filtering"],
        speedup=2.5,
        description="Uses draft models to filter prompt tokens before heavy prefill.",
        scholar_query="Cross-Family Speculative Prefill Training-Free Long-Context Compression",
    )

    def __init__(
        self,
        keep_ratio: float = 0.4,
        min_keep: int = 64,
        config: Optional[SpeculativePrefillConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = SpeculativePrefillConfig(keep_ratio=keep_ratio, min_keep=min_keep)
            self.config.validate()

        self.keep_ratio = max(0.01, min(1.0, self.config.keep_ratio))
        self.min_keep = self.config.min_keep

    def estimate_importance(self, num_tokens: int) -> List[float]:
        """Draft-model token importance proxy in [0, 1]."""
        if num_tokens <= 0:
            return []

        scores: List[float] = []
        for i in range(num_tokens):
            recency = i / max(num_tokens - 1, 1)
            salient = abs(math.sin(i * 0.3)) ** 2
            scores.append(round(min(1.0, 0.25 + (0.5 * recency) + (0.25 * salient)), 4))
        return scores

    def compress_prefill(self, num_tokens: int) -> PaperResult:
        """
        Simulate prompt prefill compression using importance scores.
        """
        if num_tokens < 1:
            return PaperResult({
                "compressed": False,
                "original_tokens": 0,
                "kept_tokens": 0,
                "dropped_tokens": 0,
                "keep_ratio": 1.0,
                "speedup_multiplier": 1.0,
                "training_free": True,
            })

        keep = max(self.min_keep, int(num_tokens * self.keep_ratio))
        keep = min(keep, num_tokens)
        dropped = num_tokens - keep
        speedup = num_tokens / keep if keep > 0 else 1.0

        return PaperResult({
            "compressed": dropped > 0,
            "original_tokens": num_tokens,
            "kept_tokens": keep,
            "dropped_tokens": dropped,
            "keep_ratio": round(keep / num_tokens, 4),
            "speedup_multiplier": round(speedup, 4),
            "training_free": True,
        })

    def filter_tokens(
        self,
        token_list: Sequence[Any],
        importance_scores: Optional[Sequence[float]] = None,
    ) -> List[Any]:
        """Filter token sequence to retain only highest importance tokens."""
        if not token_list:
            return []

        n = len(token_list)
        scores = list(importance_scores) if importance_scores is not None else self.estimate_importance(n)
        keep_count = min(n, max(self.min_keep, int(n * self.keep_ratio)))

        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = sorted([idx for idx, _ in indexed_scores[:keep_count]])

        return [token_list[i] for i in top_indices]

    def execute(self, num_tokens: int = 2048, **kwargs: Any) -> PaperResult:
        """Execute speculative prefill compression simulation."""
        n_tok = kwargs.get("num_tokens", num_tokens)
        return self.compress_prefill(n_tok)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "keep_ratio": self.keep_ratio,
            "min_keep": self.min_keep,
        }


__all__ = ["SpeculativePrefillCompressor"]
