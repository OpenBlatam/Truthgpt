"""
Budget-Aware Discriminative Verification Module
===============================================
Based on "Budget-aware Test-time Scaling via Discriminative Verification"
(arXiv:2510.14913, 2025/2026)

Key idea:
---------
Combining a lightweight discriminative verifier (scores how likely a candidate answer is correct)
with self-consistency voting in a hybrid selector yields large accuracy gains under the same budget.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import DiscriminativeVerifierConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class DiscriminativeVerifier(BasePaperModule):
    """
    Hybrid selector that blends self-consistency vote share with a
    discriminative verifier score to select optimal answers under a fixed budget.
    """

    metadata = PaperMetadata(
        paper_id="discriminative_verification",
        paper_name="Budget-aware Test-time Scaling via Discriminative Verification",
        category=PaperCategory.REASONING,
        arxiv_id="2510.14913",
        year=2025,
        authors=["Discriminative Verification Team"],
        key_techniques=["Hybrid Selector", "Self-Consistency Voting", "Discriminative Scoring"],
        speedup=1.4,
        accuracy_improvement=15.3,
        description="Blends majority vote with lightweight discriminative scoring under fixed compute.",
        scholar_query="Budget-aware Test-time Scaling Discriminative Verification",
    )

    def __init__(
        self,
        vote_weight: float = 0.5,
        verifier_weight: float = 0.5,
        config: Optional[DiscriminativeVerifierConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = DiscriminativeVerifierConfig(
                vote_weight=vote_weight,
                verifier_weight=verifier_weight,
            )
            self.config.validate()

        total = self.config.vote_weight + self.config.verifier_weight
        self.vote_weight = self.config.vote_weight / total if total > 0 else 0.5
        self.verifier_weight = self.config.verifier_weight / total if total > 0 else 0.5

    def select(self, candidates: Sequence[Tuple[str, float]]) -> PaperResult:
        """
        Select the best candidate answer using the hybrid scoring objective.
        """
        if not candidates:
            return PaperResult({
                "selected": None,
                "reason": "no candidates",
                "hybrid_score": 0.0,
                "majority_vote_answer": None,
                "overrode_majority": False,
                "num_candidates": 0,
                "num_unique_answers": 0,
                "vote_weight": round(self.vote_weight, 3),
                "verifier_weight": round(self.verifier_weight, 3),
            })

        total_votes = len(candidates)
        vote_counts: Dict[str, int] = defaultdict(int)
        score_sums: Dict[str, float] = defaultdict(float)

        for item in candidates:
            if not isinstance(item, (tuple, list)) or len(item) < 2:
                continue
            answer, score = str(item[0]), float(item[1])
            vote_counts[answer] += 1
            score_sums[answer] += max(0.0, min(1.0, score))

        if not vote_counts:
            return PaperResult({"selected": None, "reason": "invalid candidate format"})

        hybrid: Dict[str, float] = {}
        for answer, count in vote_counts.items():
            vote_share = count / total_votes
            avg_score = score_sums[answer] / count
            hybrid[answer] = (self.vote_weight * vote_share) + (self.verifier_weight * avg_score)

        selected = max(hybrid, key=lambda k: hybrid[k])
        majority = max(vote_counts, key=lambda k: vote_counts[k])

        return PaperResult({
            "selected": selected,
            "hybrid_score": round(hybrid[selected], 4),
            "majority_vote_answer": majority,
            "overrode_majority": selected != majority,
            "num_candidates": total_votes,
            "num_unique_answers": len(vote_counts),
            "vote_weight": round(self.vote_weight, 3),
            "verifier_weight": round(self.verifier_weight, 3),
        })

    def score_all(self, candidates: Sequence[Tuple[str, float]]) -> PaperResult:
        """
        Compute full breakdown of vote share, verifier score, and hybrid score for all unique answers.
        """
        if not candidates:
            return PaperResult({})

        total_votes = len(candidates)
        vote_counts: Dict[str, int] = defaultdict(int)
        score_sums: Dict[str, float] = defaultdict(float)

        for answer, score in candidates:
            ans_str = str(answer)
            vote_counts[ans_str] += 1
            score_sums[ans_str] += max(0.0, min(1.0, float(score)))

        breakdown: Dict[str, Any] = {}
        for answer, count in vote_counts.items():
            vote_share = count / total_votes
            avg_score = score_sums[answer] / count
            h_score = (self.vote_weight * vote_share) + (self.verifier_weight * avg_score)
            breakdown[answer] = {
                "votes": float(count),
                "vote_share": round(vote_share, 4),
                "avg_verifier_score": round(avg_score, 4),
                "hybrid_score": round(h_score, 4),
            }
        return PaperResult(breakdown)

    def execute(self, candidates: Optional[Sequence[Tuple[str, float]]] = None, **kwargs: Any) -> PaperResult:
        """Execute discriminative verification answer selection."""
        cands = candidates if candidates is not None else kwargs.get(
            "candidates", [("42", 0.95), ("42", 0.88), ("24", 0.30), ("42", 0.92), ("12", 0.10)]
        )
        return self.select(cands)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "vote_weight": self.vote_weight,
            "verifier_weight": self.verifier_weight,
        }


__all__ = ["DiscriminativeVerifier"]
