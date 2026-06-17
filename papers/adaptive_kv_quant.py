"""
Adaptive KV-Cache Quantization Module
Based on "Don't Waste Bits! Adaptive KV-Cache Quantization for Lightweight
On-Device LLMs" (arXiv:2604.04722, April 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=Adaptive+KV-Cache+Quantization+for+Lightweight+On-Device+LLMs

Key idea:
A uniform KV-cache bit-width either wastes bits on low-impact tokens or
over-compresses informative ones. This method allocates bit-width per token by
importance: high-impact tokens keep more bits, low-impact tokens are aggressively
quantized -- cutting KV memory/bandwidth on device with minimal quality loss.
"""

import math
from typing import Any, Dict, List


class AdaptiveKVQuantizer:
    """
    Simulates per-token adaptive KV-cache bit allocation.

    Tokens scoring above ``high_impact_threshold`` keep ``high_bits``; the rest
    get ``low_bits``. Reports memory vs an fp16 (16-bit) baseline.
    """

    def __init__(
        self,
        high_bits: int = 8,
        low_bits: int = 2,
        high_impact_threshold: float = 0.6,
        baseline_bits: int = 16,
    ):
        self.high_bits = high_bits
        self.low_bits = low_bits
        self.high_impact_threshold = high_impact_threshold
        self.baseline_bits = baseline_bits

    def estimate_token_impact(self, num_tokens: int) -> List[float]:
        """Importance proxy in [0, 1] per token (recent + sink tokens matter more)."""
        impact = []
        for i in range(num_tokens):
            recency = i / max(num_tokens - 1, 1)
            sink = 1.0 if i < 4 else 0.0  # attention-sink tokens
            score = max(sink, 0.3 + 0.5 * recency * abs(math.sin(i * 0.5)))
            impact.append(min(1.0, score))
        return impact

    def quantize(self, num_tokens: int) -> Dict[str, Any]:
        if num_tokens < 1:
            return {"quantized": False, "memory_ratio": 1.0, "bits_saved": 0}

        impact = self.estimate_token_impact(num_tokens)
        high = sum(1 for s in impact if s >= self.high_impact_threshold)
        low = num_tokens - high

        adaptive_bits = high * self.high_bits + low * self.low_bits
        baseline = num_tokens * self.baseline_bits
        memory_ratio = adaptive_bits / baseline

        return {
            "quantized": True,
            "num_tokens": num_tokens,
            "high_impact_tokens": high,
            "low_impact_tokens": low,
            "avg_bits_per_token": round(adaptive_bits / num_tokens, 3),
            "memory_ratio": round(memory_ratio, 4),
            "memory_savings_pct": round((1.0 - memory_ratio) * 100, 2),
        }
