"""
SnapKV Cache Compression Module
Based on "SnapKV: LLM Knows What You are Looking for Before Generation" (arXiv:2404.14469)
"""

import math
from typing import Any, Dict, List

class SnapKVCacheCompressor:
    """
    Simulates SnapKV compression by identifying and keeping important observation windows
    and key tokens based on a voting mechanism in the attention layer.
    """
    
    def __init__(self, observation_window: int = 32, compression_rate: float = 0.5):
        self.observation_window = observation_window
        self.compression_rate = compression_rate
        
    def calculate_attention_votes(self, context_length: int) -> List[float]:
        """Simulates the attention voting mechanism that finds important tokens."""
        # Tokens near the end or with specific structural importance get higher votes
        votes = []
        for i in range(context_length):
            # Simulated heuristic: recent tokens and beginning tokens are more important
            if i < 10 or i > context_length - self.observation_window:
                votes.append(1.0)
            else:
                # Randomize slightly but keep it lower for middle tokens
                votes.append(0.3 + 0.2 * abs(math.sin(i)))
        return votes
        
    def compress_kv_cache(self, current_tokens: int) -> Dict[str, Any]:
        """
        Compresses the KV cache based on the compression rate.
        Returns metrics on how many tokens were compressed.
        """
        if current_tokens < self.observation_window * 2:
            return {
                "compressed": False,
                "original_size": current_tokens,
                "new_size": current_tokens,
                "compression_ratio": 1.0
            }
            
        votes = self.calculate_attention_votes(current_tokens)
        
        # Sort indices by vote score
        indexed_votes = list(enumerate(votes))
        indexed_votes.sort(key=lambda x: x[1], reverse=True)
        
        target_size = int(current_tokens * self.compression_rate)
        # We must keep at least the observation window
        target_size = max(target_size, self.observation_window)
        
        return {
            "compressed": True,
            "original_size": current_tokens,
            "new_size": target_size,
            "compression_ratio": target_size / current_tokens,
            "tokens_saved": current_tokens - target_size
        }
