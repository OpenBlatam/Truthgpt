"""
Budget-Aware Discriminative Verification Module
Based on "Budget-aware Test-time Scaling via Discriminative Verification"
(arXiv:2510.14913, 2025/2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Budget-aware+Test-time+Scaling+via+Discriminative+Verification

Key idea:
Self-consistency (majority vote) and generative verification each have weaknesses
under a fixed compute budget. Combining a cheap *discriminative* verifier (scores
how likely a candidate answer is correct) with self-consistency voting in a hybrid
selector yields large accuracy gains under the *same* budget -- the paper reports
up to +15.3% on AIME2025 vs SOTA generative verification at equal compute.
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple


class DiscriminativeVerifier:
    """
    Simulates a hybrid selector that blends self-consistency vote share with a
    discriminative verifier score to pick the final answer under a fixed budget.
    """

    def __init__(self, vote_weight: float = 0.5, verifier_weight: float = 0.5):
        total = vote_weight + verifier_weight
        # Normalize so the two signals form a convex combination.
        self.vote_weight = vote_weight / total if total else 0.5
        self.verifier_weight = verifier_weight / total if total else 0.5

    def select(self, candidates: List[Tuple[str, float]]) -> Dict[str, Any]:
        """
        Args:
            candidates: list of (answer, verifier_score) where verifier_score in [0, 1].
                        Repeated answers contribute to the self-consistency vote.

        Returns:
            The hybrid-selected answer plus the pure-vote baseline for comparison.
        """
        if not candidates:
            return {"selected": None, "reason": "no candidates"}

        total_votes = len(candidates)
        vote_counts: Dict[str, int] = defaultdict(int)
        score_sums: Dict[str, float] = defaultdict(float)
        for answer, score in candidates:
            vote_counts[answer] += 1
            score_sums[answer] += max(0.0, min(1.0, score))

        hybrid: Dict[str, float] = {}
        for answer in vote_counts:
            vote_share = vote_counts[answer] / total_votes
            avg_score = score_sums[answer] / vote_counts[answer]
            hybrid[answer] = (
                self.vote_weight * vote_share + self.verifier_weight * avg_score
            )

        selected = max(hybrid, key=hybrid.get)
        majority = max(vote_counts, key=vote_counts.get)

        return {
            "selected": selected,
            "hybrid_score": round(hybrid[selected], 4),
            "majority_vote_answer": majority,
            "overrode_majority": selected != majority,
            "num_candidates": total_votes,
            "num_unique_answers": len(vote_counts),
            "vote_weight": round(self.vote_weight, 3),
            "verifier_weight": round(self.verifier_weight, 3),
        }
