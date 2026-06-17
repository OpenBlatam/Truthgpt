"""
INTUITOR - Reinforcement Learning from Internal Feedback (Self-Certainty)
Based on "Learning to Reason without External Rewards" (arXiv:2505.19590, ICLR 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Learning+to+Reason+without+External+Rewards+INTUITOR+self-certainty

Key idea:
INTUITOR replaces external/verifiable rewards with the model's *own* confidence
("self-certainty") as the sole intrinsic reward signal for GRPO-style RL. Despite
using no gold labels or verifiers, it matches supervised RLVR (e.g. GRPO) on math
reasoning and generalizes better out-of-domain. Self-certainty is measured as the
KL divergence of the token distribution from uniform (sharper = more certain).
"""

import math
from typing import Any, Dict, List


class IntuitorReward:
    """
    Computes the self-certainty intrinsic reward used by INTUITOR and simulates
    a GRPO-style group-relative advantage from it (label-free).
    """

    def __init__(self, vocab_size: int = 32000):
        self.vocab_size = vocab_size
        self.uniform_logprob = -math.log(vocab_size)

    def self_certainty(self, token_probs: List[float]) -> float:
        """
        Self-certainty = average KL(distribution || uniform) over generated tokens.
        Higher means the model committed confidently. ``token_probs`` is the
        probability the model assigned to each token it actually emitted.
        """
        if not token_probs:
            return 0.0
        kl = 0.0
        for p in token_probs:
            p = min(max(p, 1e-9), 1.0)
            # Per-token contribution: log p(token) - log(1/V)
            kl += math.log(p) - self.uniform_logprob
        return kl / len(token_probs)

    def group_advantages(self, group_rewards: List[float]) -> List[float]:
        """GRPO-style group-relative advantage: normalize rewards within the group."""
        if not group_rewards:
            return []
        mean = sum(group_rewards) / len(group_rewards)
        var = sum((r - mean) ** 2 for r in group_rewards) / len(group_rewards)
        std = math.sqrt(var) + 1e-8
        return [round((r - mean) / std, 4) for r in group_rewards]

    def score_group(self, group_token_probs: List[List[float]]) -> Dict[str, Any]:
        """Score a group of sampled rollouts using only self-certainty (no labels)."""
        rewards = [self.self_certainty(tp) for tp in group_token_probs]
        advantages = self.group_advantages(rewards)
        best = max(range(len(rewards)), key=lambda i: rewards[i]) if rewards else -1
        return {
            "rewards": [round(r, 4) for r in rewards],
            "advantages": advantages,
            "best_rollout": best,
            "label_free": True,
            "group_size": len(rewards),
        }
