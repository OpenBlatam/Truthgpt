"""
Distinct Leaf Enumeration (DLE) Module
Based on "Efficient Test-Time Inference via Deterministic Exploration of
Truncated Decoding Trees" (arXiv:2604.20500, 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Deterministic+Exploration+of+Truncated+Decoding+Trees

Key idea:
Self-consistency samples many reasoning traces with replacement and votes.
Because sampling revisits the same high-probability prefixes, a large fraction
of the sampled completions are duplicates -> wasted compute. DLE treats
truncated sampling as a traversal of a pruned decoding tree and *deterministically
enumerates distinct leaves*, so every generated trace is unique. This recovers
the diversity self-consistency needs while spending far less compute.
"""

import math
from typing import Any, Dict


class DistinctLeafEnumerator:
    """
    Simulates the compute savings of replacing sampling-with-replacement
    self-consistency with deterministic distinct-leaf enumeration.
    """

    def __init__(self, duplication_rate: float = 0.45):
        # Empirical fraction of sampled completions that are duplicates under
        # vanilla self-consistency (with-replacement). Paper reports this is large.
        self.duplication_rate = max(0.0, min(0.95, duplication_rate))

    def expected_distinct(self, num_samples: int) -> int:
        """Expected number of *distinct* traces under sampling-with-replacement."""
        # Coupon-collector style decay of distinct yield as samples grow.
        unique_fraction = (1.0 - self.duplication_rate) ** 0.0  # base
        distinct = num_samples * (1.0 - self.duplication_rate * (1.0 - math.exp(-num_samples / 8.0)))
        return max(1, int(round(distinct)))

    def enumerate_leaves(self, sample_budget: int) -> Dict[str, Any]:
        """
        Compare with-replacement sampling vs deterministic distinct enumeration
        for a fixed *number of distinct traces* target.

        DLE produces ``sample_budget`` distinct traces directly; vanilla
        self-consistency must oversample to reach the same distinct count.
        """
        if sample_budget < 1:
            sample_budget = 1

        # Vanilla: how many raw samples to reach `sample_budget` distinct traces.
        # Invert the duplication so we know the oversampling factor.
        oversample_factor = 1.0 / max(1e-6, (1.0 - self.duplication_rate))
        vanilla_samples = int(math.ceil(sample_budget * oversample_factor))

        compute_saved = vanilla_samples - sample_budget
        savings_ratio = compute_saved / vanilla_samples if vanilla_samples else 0.0

        return {
            "distinct_traces": sample_budget,
            "vanilla_samples_needed": vanilla_samples,
            "samples_saved": compute_saved,
            "compute_savings_ratio": round(savings_ratio, 4),
            "speedup_multiplier": round(oversample_factor, 4),
            "deterministic": True,
        }
