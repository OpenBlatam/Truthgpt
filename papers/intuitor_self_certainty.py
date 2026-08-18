"""
INTUITOR - Reinforcement Learning from Internal Feedback (Self-Certainty)
=========================================================================
Based on "Learning to Reason without External Rewards" (arXiv:2505.19590, ICLR 2026)

Key idea:
---------
INTUITOR replaces external/verifiable rewards with the model's own confidence
("self-certainty") as the sole intrinsic reward signal for GRPO-style RL.
Measured as the KL divergence of the token distribution from uniform.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import IntuitorConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class IntuitorReward(BasePaperModule):
    """
    Computes self-certainty intrinsic reward and simulates GRPO-style group advantages label-free.
    """

    metadata = PaperMetadata(
        paper_id="intuitor_self_certainty",
        paper_name="Learning to Reason without External Rewards (INTUITOR)",
        category=PaperCategory.RL_ALIGNMENT,
        arxiv_id="2505.19590",
        year=2025,
        authors=["INTUITOR Authors"],
        key_techniques=["Self-Certainty Reward", "KL from Uniform", "Label-Free GRPO"],
        speedup=1.3,
        accuracy_improvement=6.8,
        description="Employs internal token certainty as an intrinsic reward for GRPO reasoning.",
        scholar_query="Learning to Reason without External Rewards INTUITOR self-certainty",
    )

    def __init__(
        self,
        vocab_size: int = 32000,
        config: Optional[IntuitorConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = IntuitorConfig(vocab_size=vocab_size)
            self.config.validate()

        self.vocab_size = self.config.vocab_size
        self.uniform_logprob = -math.log(self.vocab_size)

    def self_certainty(self, token_probs: Sequence[float]) -> float:
        """Self-certainty = average KL(distribution || uniform) over generated tokens."""
        if not token_probs:
            return 0.0
        kl = 0.0
        for p in token_probs:
            p_clamped = min(max(float(p), 1e-9), 1.0)
            kl += math.log(p_clamped) - self.uniform_logprob
        return float(kl / len(token_probs))

    @staticmethod
    def group_advantages(group_rewards: Sequence[float]) -> List[float]:
        """GRPO-style group-relative advantage: normalize rewards within the group."""
        if not group_rewards:
            return []
        if len(group_rewards) == 1:
            return [0.0]

        mean = sum(group_rewards) / len(group_rewards)
        var = sum((r - mean) ** 2 for r in group_rewards) / len(group_rewards)
        std = math.sqrt(var) + 1e-8
        return [round((r - mean) / std, 4) for r in group_rewards]

    def score_group(self, group_token_probs: Sequence[Sequence[float]]) -> PaperResult:
        """
        Score a group of sampled rollouts using self-certainty without gold labels.
        """
        if not group_token_probs:
            return PaperResult({
                "rewards": [],
                "advantages": [],
                "best_rollout": -1,
                "label_free": True,
                "group_size": 0,
            })

        rewards = [self.self_certainty(tp) for tp in group_token_probs]
        advantages = self.group_advantages(rewards)
        best = max(range(len(rewards)), key=lambda i: rewards[i]) if rewards else -1

        return PaperResult({
            "rewards": [round(r, 4) for r in rewards],
            "advantages": advantages,
            "best_rollout": best,
            "label_free": True,
            "group_size": len(rewards),
        })

    def execute(self, group_token_probs: Optional[Sequence[Sequence[float]]] = None, **kwargs: Any) -> PaperResult:
        """Execute intuitor self-certainty group scoring."""
        groups = group_token_probs if group_token_probs is not None else kwargs.get(
            "group_token_probs",
            [
                [0.9, 0.85, 0.95, 0.88],
                [0.4, 0.35, 0.50, 0.42],
                [0.7, 0.75, 0.80, 0.72],
            ],
        )
        return self.score_group(groups)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "vocab_size": self.vocab_size,
            "uniform_logprob": round(self.uniform_logprob, 4),
        }


__all__ = ["IntuitorReward"]
