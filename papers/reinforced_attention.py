"""
RAL - Reinforced Attention Learning
Based on "Reinforced Attention Learning" (arXiv:2602.04884, Feb 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Reinforced+Attention+Learning

Key idea:
Instead of only updating output-token policies, RAL applies the RL reward signal to
the *attention* distribution itself, reinforcing the heads/positions that
contribute to correct reasoning. This consistently beats the base model and plain
GRPO across reasoning benchmarks by steering where the model looks.
"""

import math
from typing import Any, Dict, List


class ReinforcedAttentionLearner:
    """
    Simulates reward-weighted reinforcement of attention head contributions.
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate

    def reinforce(self, head_contributions: List[float], reward: float) -> Dict[str, Any]:
        """
        head_contributions: per-head contribution scores to the (correct) answer.
        reward: scalar reward for the rollout (e.g. +1 correct, -1 wrong).

        Returns updated, renormalized attention weights over heads.
        """
        if not head_contributions:
            return {"updated_weights": [], "reinforced_heads": 0}

        n = len(head_contributions)
        base = [1.0 / n] * n  # start from uniform allocation
        # Policy-gradient style nudge toward contributing heads, scaled by reward.
        updated = [
            max(1e-6, w + self.learning_rate * reward * (c - sum(head_contributions) / n))
            for w, c in zip(base, head_contributions)
        ]
        z = sum(updated)
        updated = [u / z for u in updated]

        reinforced = sum(1 for u, b in zip(updated, base) if u > b)
        # Entropy of resulting attention allocation (lower => more focused).
        ent = -sum(u * math.log(u) for u in updated if u > 0) / math.log(n) if n > 1 else 0.0

        return {
            "updated_weights": [round(u, 4) for u in updated],
            "reinforced_heads": reinforced,
            "num_heads": n,
            "attention_entropy": round(ent, 4),
            "reward_applied": reward,
        }
