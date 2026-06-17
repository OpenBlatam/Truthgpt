"""
ECHO - Entropy-Confidence Hybrid Optimization for Test-Time RL
Based on "ECHO: Entropy-Confidence Hybrid Optimization for Test-Time
Reinforcement Learning" (arXiv:2602.02150, Feb 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=ECHO+Entropy-Confidence+Hybrid+Optimization+Test-Time+Reinforcement+Learning

Key idea:
Test-time RL (adapting on the fly without labels) needs a reward proxy. Pure
confidence rewards collapse to over-confident wrong answers; pure entropy rewards
are noisy. ECHO blends *confidence* (exploit certain answers) with *entropy*
(preserve exploration) into a hybrid reward, giving stable test-time updates.
"""

import math
from typing import Any, Dict, List


class EchoOptimizer:
    """
    Computes ECHO's entropy-confidence hybrid reward for a set of rollouts and
    selects/weights them for a test-time RL update.
    """

    def __init__(self, confidence_weight: float = 0.6, entropy_weight: float = 0.4):
        total = confidence_weight + entropy_weight
        self.confidence_weight = confidence_weight / total if total else 0.6
        self.entropy_weight = entropy_weight / total if total else 0.4

    @staticmethod
    def _normalized_entropy(dist: List[float]) -> float:
        """Shannon entropy normalized to [0, 1] by log(n)."""
        probs = [p for p in dist if p > 0]
        if len(probs) <= 1:
            return 0.0
        h = -sum(p * math.log(p) for p in probs)
        return h / math.log(len(probs))

    def hybrid_reward(self, confidence: float, dist: List[float]) -> float:
        """confidence in [0,1]; dist is an answer distribution for the rollout."""
        h = self._normalized_entropy(dist)
        # Reward high confidence but keep some entropy to avoid collapse.
        return self.confidence_weight * confidence + self.entropy_weight * h

    def optimize(self, rollouts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        rollouts: list of {"confidence": float, "dist": [probs...]}.
        Returns hybrid rewards, the selected rollout, and a softmax update weight.
        """
        if not rollouts:
            return {"selected": -1, "rewards": []}

        rewards = [self.hybrid_reward(r.get("confidence", 0.0), r.get("dist", [])) for r in rollouts]
        m = max(rewards)
        exps = [math.exp(r - m) for r in rewards]
        z = sum(exps)
        weights = [round(e / z, 4) for e in exps]
        selected = max(range(len(rewards)), key=lambda i: rewards[i])

        return {
            "rewards": [round(r, 4) for r in rewards],
            "update_weights": weights,
            "selected": selected,
            "confidence_weight": round(self.confidence_weight, 3),
            "entropy_weight": round(self.entropy_weight, 3),
            "label_free": True,
        }
