"""
ECHO - Entropy-Confidence Hybrid Optimization for Test-Time RL
==============================================================
Based on "ECHO: Entropy-Confidence Hybrid Optimization for Test-Time
Reinforcement Learning" (arXiv:2602.02150, Feb 2026)

Key idea:
---------
ECHO blends confidence (exploit certain answers) with entropy (preserve exploration)
into a hybrid reward, giving stable test-time updates without gold labels.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import EchoOptimizerConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class EchoOptimizer(BasePaperModule):
    """
    Computes ECHO's entropy-confidence hybrid reward for rollouts and
    selects/weights them for a test-time RL update.
    """

    metadata = PaperMetadata(
        paper_id="echo_ttrl",
        paper_name="ECHO: Entropy-Confidence Hybrid Optimization for Test-Time Reinforcement Learning",
        category=PaperCategory.RL_ALIGNMENT,
        arxiv_id="2602.02150",
        year=2026,
        authors=["ECHO Authors"],
        key_techniques=["Hybrid Entropy-Confidence", "Test-Time RL", "Collapse Prevention"],
        speedup=1.2,
        accuracy_improvement=5.1,
        description="Blends confidence and entropy rewards to adapt models reliably at test-time.",
        scholar_query="ECHO Entropy-Confidence Hybrid Optimization Test-Time Reinforcement Learning",
    )

    def __init__(
        self,
        confidence_weight: float = 0.6,
        entropy_weight: float = 0.4,
        config: Optional[EchoOptimizerConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = EchoOptimizerConfig(
                confidence_weight=confidence_weight,
                entropy_weight=entropy_weight,
            )
            self.config.validate()

        total = self.config.confidence_weight + self.config.entropy_weight
        self.confidence_weight = self.config.confidence_weight / total if total > 0 else 0.6
        self.entropy_weight = self.config.entropy_weight / total if total > 0 else 0.4

    @staticmethod
    def _normalized_entropy(dist: Sequence[float]) -> float:
        """Compute Shannon entropy normalized to [0, 1] by log(n)."""
        if not dist:
            return 0.0
        probs = [p for p in dist if p > 0.0]
        if len(probs) <= 1:
            return 0.0
        h = -sum(p * math.log(p) for p in probs)
        return float(h / math.log(len(probs)))

    def hybrid_reward(self, confidence: float, dist: Sequence[float]) -> float:
        """Compute scalar hybrid reward balancing certainty and exploration."""
        conf_clamped = max(0.0, min(1.0, float(confidence)))
        h = self._normalized_entropy(dist)
        return float((self.confidence_weight * conf_clamped) + (self.entropy_weight * h))

    def optimize(self, rollouts: Sequence[Dict[str, Any]]) -> PaperResult:
        """
        Score a batch of candidate rollouts and calculate softmax update weights.
        """
        if not rollouts:
            return PaperResult({
                "selected": -1,
                "rewards": [],
                "update_weights": [],
                "confidence_weight": round(self.confidence_weight, 3),
                "entropy_weight": round(self.entropy_weight, 3),
                "label_free": True,
            })

        rewards = [self.hybrid_reward(r.get("confidence", 0.0), r.get("dist", [])) for r in rollouts]
        max_r = max(rewards)
        exps = [math.exp(r - max_r) for r in rewards]
        sum_exp = sum(exps)
        weights = [round(e / sum_exp, 4) for e in exps] if sum_exp > 0 else [1.0 / len(rewards)] * len(rewards)
        selected = max(range(len(rewards)), key=lambda i: rewards[i])

        return PaperResult({
            "rewards": [round(r, 4) for r in rewards],
            "update_weights": weights,
            "selected": selected,
            "confidence_weight": round(self.confidence_weight, 3),
            "entropy_weight": round(self.entropy_weight, 3),
            "label_free": True,
        })

    def execute(self, rollouts: Optional[Sequence[Dict[str, Any]]] = None, **kwargs: Any) -> PaperResult:
        """Execute ECHO optimization over rollouts."""
        sample_rollouts = rollouts if rollouts is not None else kwargs.get(
            "rollouts",
            [
                {"confidence": 0.85, "dist": [0.8, 0.1, 0.05, 0.05]},
                {"confidence": 0.50, "dist": [0.3, 0.3, 0.2, 0.2]},
                {"confidence": 0.92, "dist": [0.9, 0.05, 0.03, 0.02]},
            ],
        )
        return self.optimize(sample_rollouts)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "confidence_weight": self.confidence_weight,
            "entropy_weight": self.entropy_weight,
        }


__all__ = ["EchoOptimizer"]
