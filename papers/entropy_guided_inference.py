"""
Entropy-Guided Adaptive Inference Module
Based on "From Rigid to Dynamic: Entropy-Guided Adaptive Inference for Long-Context LLMs"
(arXiv:2606.09508v1, June 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Entropy-Guided+Adaptive+Inference+for+Long-Context+LLMs

Key idea (EntropyInfer):
Attention entropy varies a lot across heads and across segments of a long prompt.
Low-entropy (sharply focused) heads/segments carry little extra information when
computed at full density, so compute can be allocated adaptively: spend full
attention on high-entropy regions and use sparse attention on low-entropy ones.
This is training-free and yields up to ~2.39x end-to-end speedup beyond 100k
tokens with minimal quality degradation.
"""

import math
from typing import Any, Dict, List


class EntropyGuidedInference:
    """
    Simulates entropy-guided adaptive compute allocation during prefill.

    For each segment of the context an attention-entropy proxy is estimated.
    Segments whose entropy falls below ``entropy_threshold`` are served with
    sparse attention (cheaper), the rest keep full attention. The resulting
    compute budget and end-to-end speedup are reported.
    """

    def __init__(
        self,
        entropy_threshold: float = 0.55,
        sparse_cost_ratio: float = 0.25,
        max_speedup: float = 2.39,
    ):
        # Normalized entropy below this => segment treated as "focused" -> sparse
        self.entropy_threshold = entropy_threshold
        # Relative cost of a sparse segment vs a full-attention segment
        self.sparse_cost_ratio = sparse_cost_ratio
        # Cap matching the paper's reported end-to-end speedup
        self.max_speedup = max_speedup

    def estimate_segment_entropy(self, num_segments: int) -> List[float]:
        """Estimate a normalized [0, 1] attention-entropy proxy per segment."""
        entropies = []
        for i in range(num_segments):
            # Heuristic: prompt boundaries (start/end) tend to be high-entropy
            # (broad attention), while the bulk middle is more focused/repetitive.
            position = i / max(num_segments - 1, 1)
            boundary = 1.0 - abs(position - 0.5) * 2.0  # 0 at edges, 1 at center
            focused = 0.5 + 0.45 * abs(math.cos(i * 0.7))
            entropies.append(round(max(0.0, min(1.0, focused - 0.3 * boundary)), 4))
        return entropies

    def allocate_compute(self, context_length: int, segment_size: int = 1024) -> Dict[str, Any]:
        """
        Decide per-segment attention density and report the projected speedup.
        """
        num_segments = max(1, math.ceil(context_length / segment_size))
        entropies = self.estimate_segment_entropy(num_segments)

        full_segments = [i for i, e in enumerate(entropies) if e >= self.entropy_threshold]
        sparse_segments = [i for i, e in enumerate(entropies) if e < self.entropy_threshold]

        # Cost relative to dense full-attention over all segments (== num_segments).
        adaptive_cost = len(full_segments) + len(sparse_segments) * self.sparse_cost_ratio
        dense_cost = float(num_segments)
        raw_speedup = dense_cost / adaptive_cost if adaptive_cost > 0 else 1.0
        speedup = min(raw_speedup, self.max_speedup)

        return {
            "context_length": context_length,
            "num_segments": num_segments,
            "full_attention_segments": len(full_segments),
            "sparse_attention_segments": len(sparse_segments),
            "compute_fraction": round(adaptive_cost / dense_cost, 4),
            "speedup_multiplier": round(speedup, 4),
            "training_free": True,
        }
