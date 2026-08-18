"""
RAL - Reinforced Attention Learning
===================================
Based on "Reinforced Attention Learning" (arXiv:2602.04884, Feb 2026)

Key idea:
---------
Applies the RL reward signal directly to the attention distribution itself,
reinforcing the heads/positions that contribute to correct reasoning.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import ReinforcedAttentionConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class ReinforcedAttentionLearner(BasePaperModule):
    """
    Simulates reward-weighted reinforcement of attention head contributions.
    """

    metadata = PaperMetadata(
        paper_id="reinforced_attention",
        paper_name="Reinforced Attention Learning",
        category=PaperCategory.RL_ALIGNMENT,
        arxiv_id="2602.04884",
        year=2026,
        authors=["RAL Authors"],
        key_techniques=["Attention Distribution RL", "Head Contribution Weighting", "Steered Focus"],
        speedup=1.2,
        accuracy_improvement=4.2,
        description="Applies RL rewards directly to attention heads to reinforce relevant reasoning paths.",
        scholar_query="Reinforced Attention Learning",
    )

    def __init__(
        self,
        learning_rate: float = 0.1,
        config: Optional[ReinforcedAttentionConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = ReinforcedAttentionConfig(learning_rate=learning_rate)
            self.config.validate()

        self.learning_rate = self.config.learning_rate

    def reinforce(self, head_contributions: Sequence[float], reward: float = 1.0) -> PaperResult:
        """
        Update and renormalize attention head weights using policy-gradient style reward signal.
        """
        if not head_contributions:
            return PaperResult({
                "updated_weights": [],
                "reinforced_heads": 0,
                "num_heads": 0,
                "attention_entropy": 0.0,
                "reward_applied": reward,
            })

        n = len(head_contributions)
        base = [1.0 / n] * n
        avg_contrib = sum(head_contributions) / n

        updated = [
            max(1e-6, w + (self.learning_rate * float(reward) * (c - avg_contrib)))
            for w, c in zip(base, head_contributions)
        ]
        total_w = sum(updated)
        updated = [u / total_w for u in updated]

        reinforced = sum(1 for u, b in zip(updated, base) if u > b)
        ent = -sum(u * math.log(u) for u in updated if u > 0.0) / math.log(n) if n > 1 else 0.0

        return PaperResult({
            "updated_weights": [round(u, 4) for u in updated],
            "reinforced_heads": reinforced,
            "num_heads": n,
            "attention_entropy": round(ent, 4),
            "reward_applied": reward,
        })

    def reinforce_tensors(self, head_weights_tensor: Any, rewards_tensor: Any) -> Any:
        """Apply reward updates directly to PyTorch tensor representing multi-head attention weights."""
        try:
            import torch
            if isinstance(head_weights_tensor, torch.Tensor):
                mean_w = head_weights_tensor.mean(dim=1, keepdim=True)
                step = self.learning_rate * rewards_tensor * (head_weights_tensor - mean_w)
                updated = torch.clamp(head_weights_tensor + step, min=1e-6)
                return updated / updated.sum(dim=1, keepdim=True)
        except ImportError:
            pass
        return head_weights_tensor

    def execute(self, head_contributions: Optional[Sequence[float]] = None, reward: float = 1.0, **kwargs: Any) -> PaperResult:
        """Execute reinforced attention learning."""
        contribs = head_contributions if head_contributions is not None else kwargs.get(
            "head_contributions", [0.1, 0.4, 0.05, 0.25, 0.05, 0.05, 0.05, 0.05]
        )
        r = kwargs.get("reward", reward)
        return self.reinforce(contribs, reward=r)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "learning_rate": self.learning_rate,
        }


__all__ = ["ReinforcedAttentionLearner"]
