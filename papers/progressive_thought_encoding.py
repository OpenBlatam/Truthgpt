"""
PTE - Progressive Thought Encoding
Based on "Training Large Reasoning Models Efficiently via Progressive Thought
Encoding" (arXiv:2602.16839, Feb 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Training+Large+Reasoning+Models+Efficiently+Progressive+Thought+Encoding

Key idea:
Long chain-of-thought traces are expensive to train on. PTE applies a curriculum
that *progressively encodes* (compresses) verbose thoughts into denser
representations across training stages, so the model learns the same reasoning
with far fewer thought tokens -- cutting training cost while keeping accuracy.
"""

from typing import Any, Dict, List


class ProgressiveThoughtEncoder:
    """
    Simulates the progressive compression curriculum over training stages.
    """

    def __init__(self, num_stages: int = 4, final_compression: float = 0.3):
        # final_compression: fraction of original thought length kept at last stage.
        self.num_stages = max(1, num_stages)
        self.final_compression = max(0.05, min(1.0, final_compression))

    def curriculum(self, base_thought_tokens: int) -> Dict[str, Any]:
        """
        Returns the per-stage thought-token budget and total training-token savings
        vs training every stage at full length.
        """
        if base_thought_tokens < 1:
            base_thought_tokens = 1

        stages: List[Dict[str, Any]] = []
        for s in range(self.num_stages):
            # Linearly anneal from 1.0 down to final_compression.
            frac = 1.0 - (1.0 - self.final_compression) * (s / max(self.num_stages - 1, 1))
            tokens = max(1, int(round(base_thought_tokens * frac)))
            stages.append({"stage": s, "keep_fraction": round(frac, 4), "thought_tokens": tokens})

        used = sum(st["thought_tokens"] for st in stages)
        full = base_thought_tokens * self.num_stages
        savings = (full - used) / full if full else 0.0

        return {
            "base_thought_tokens": base_thought_tokens,
            "num_stages": self.num_stages,
            "stages": stages,
            "final_thought_tokens": stages[-1]["thought_tokens"],
            "training_token_savings_pct": round(savings * 100, 2),
        }
