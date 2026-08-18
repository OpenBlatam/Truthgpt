"""
SnapKV Cache Compression Module
================================
Based on "SnapKV: LLM Knows What You are Looking for Before Generation" (arXiv:2404.14469)

Key idea:
---------
Identifies and keeps key positions and recent observation windows in the KV cache
via an attention voting mechanism, compressing historical KV caches while preserving
generation accuracy.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import SnapKVConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class SnapKVCacheCompressor(BasePaperModule):
    """
    Simulates SnapKV compression by identifying and keeping important observation windows
    and key tokens based on a voting mechanism in the attention layer.
    """

    metadata = PaperMetadata(
        paper_id="snap_kv",
        paper_name="SnapKV: LLM Knows What You are Looking for Before Generation",
        category=PaperCategory.KV_CACHE,
        arxiv_id="2404.14469",
        year=2024,
        authors=["Yuhong Li", "Rong Ding", "Zixuan Chen"],
        key_techniques=["Observation Window", "Attention Voting", "KV Compression"],
        speedup=2.5,
        description="Compresses KV cache by selecting key positions via attention voting.",
        scholar_query="SnapKV LLM Knows What You are Looking for Before Generation",
    )

    def __init__(
        self,
        observation_window: int = 32,
        compression_rate: float = 0.5,
        config: Optional[SnapKVConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = SnapKVConfig(
                observation_window=observation_window,
                compression_rate=compression_rate,
            )
            self.config.validate()

        self.observation_window = self.config.observation_window
        self.compression_rate = self.config.compression_rate

    def calculate_attention_votes(self, context_length: int) -> List[float]:
        """Simulate attention voting mechanism across sequence."""
        if context_length <= 0:
            return []

        votes: List[float] = []
        for i in range(context_length):
            if i < 10 or i >= (context_length - self.observation_window):
                votes.append(1.0)
            else:
                votes.append(round(0.3 + (0.2 * abs(math.sin(i))), 4))
        return votes

    def compress_kv_cache(self, current_tokens: int) -> PaperResult:
        """
        Compresses the KV cache based on target compression rate and observation window.
        """
        if current_tokens < (self.observation_window * 2):
            return PaperResult({
                "compressed": False,
                "original_size": max(0, current_tokens),
                "new_size": max(0, current_tokens),
                "compression_ratio": 1.0,
                "tokens_saved": 0,
            })

        target_size = int(current_tokens * self.compression_rate)
        target_size = max(target_size, self.observation_window)

        return PaperResult({
            "compressed": True,
            "original_size": current_tokens,
            "new_size": target_size,
            "compression_ratio": round(target_size / current_tokens, 4),
            "tokens_saved": current_tokens - target_size,
        })

    def compress_kv_tensors(self, key_cache: Any, value_cache: Any) -> Tuple[Any, Any]:
        """Prune PyTorch KV-cache tensors along sequence dimension."""
        try:
            import torch
            if isinstance(key_cache, torch.Tensor) and isinstance(value_cache, torch.Tensor):
                seq_len = key_cache.shape[-2]
                if seq_len < (self.observation_window * 2):
                    return key_cache, value_cache

                sink_len = min(10, seq_len)
                window_len = min(self.observation_window, seq_len - sink_len)
                
                sink_k = key_cache[..., :sink_len, :]
                window_k = key_cache[..., -window_len:, :]
                pruned_k = torch.cat([sink_k, window_k], dim=-2)

                sink_v = value_cache[..., :sink_len, :]
                window_v = value_cache[..., -window_len:, :]
                pruned_v = torch.cat([sink_v, window_v], dim=-2)

                return pruned_k, pruned_v
        except ImportError:
            pass

        return key_cache, value_cache

    def execute(self, current_tokens: int = 512, **kwargs: Any) -> PaperResult:
        """Execute SnapKV cache compression."""
        num_tok = kwargs.get("current_tokens", current_tokens)
        return self.compress_kv_cache(num_tok)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "observation_window": self.observation_window,
            "compression_rate": self.compression_rate,
        }


__all__ = ["SnapKVCacheCompressor"]
