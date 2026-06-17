"""
Cross-Family Speculative Prefill Module
Based on "Cross-Family Speculative Prefill: Training-Free Long-Context
Compression with Small Draft Models" (arXiv:2603.02631, 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Cross-Family+Speculative+Prefill+Training-Free+Long-Context+Compression

Key idea:
Use a small (possibly different-family) draft model at inference time to estimate
token-level importance over a long prompt, then prefill only the most important
tokens into the large model. Training-free long-context compression that shrinks
the prefill cost while preserving the tokens that matter.
"""

import math
from typing import Any, Dict, List


class SpeculativePrefillCompressor:
    """
    Simulates draft-model-guided prefill compression: keep the top-``keep_ratio``
    most important prompt tokens, drop the rest before prefill.
    """

    def __init__(self, keep_ratio: float = 0.4, min_keep: int = 64):
        self.keep_ratio = max(0.01, min(1.0, keep_ratio))
        self.min_keep = min_keep

    def estimate_importance(self, num_tokens: int) -> List[float]:
        """Draft-model token importance proxy in [0, 1]."""
        scores = []
        for i in range(num_tokens):
            recency = i / max(num_tokens - 1, 1)
            # Recent tokens + periodic salient tokens score higher.
            salient = abs(math.sin(i * 0.3)) ** 2
            scores.append(min(1.0, 0.25 + 0.5 * recency + 0.25 * salient))
        return scores

    def compress_prefill(self, num_tokens: int) -> Dict[str, Any]:
        if num_tokens < 1:
            return {"compressed": False, "kept_tokens": 0, "speedup_multiplier": 1.0}

        keep = max(self.min_keep, int(num_tokens * self.keep_ratio))
        keep = min(keep, num_tokens)
        dropped = num_tokens - keep

        # Prefill compute ~ scales with sequence length (attention is super-linear,
        # but we report a conservative linear-in-tokens proxy).
        speedup = num_tokens / keep if keep else 1.0

        return {
            "compressed": dropped > 0,
            "original_tokens": num_tokens,
            "kept_tokens": keep,
            "dropped_tokens": dropped,
            "keep_ratio": round(keep / num_tokens, 4),
            "speedup_multiplier": round(speedup, 4),
            "training_free": True,
        }
