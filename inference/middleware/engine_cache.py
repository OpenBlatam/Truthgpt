"""
Engine Cache Middleware

Provides a centralized caching layer for all inference engines,
leveraging the Polyglot Rust KV cache if available.
"""
import logging
from typing import List, Optional, Union, Any
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

try:
    from optimization_core.polyglot.kv_cache import KVCache
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False
    logger.warning("Polyglot Rust KV cache not available.")

class EngineCacheMiddleware:
    """
    Middleware to inject Rust KV cache into any inference engine.
    """
    
    def __init__(self, max_size: int = 16384, enable_compression: bool = True):
        self.cache = None
        if POLYGLOT_AVAILABLE:
            try:
                self.cache = KVCache(
                    max_size=max_size,
                    eviction_strategy="adaptive",
                    enable_compression=enable_compression,
                )
                logger.info("External Rust KV cache initialized for Engine Cache Middleware")
            except Exception as e:
                logger.warning(f"Failed to initialize external cache: {e}")
                
    def get_from_cache(self, prompts: List[str]) -> Optional[List[str]]:
        if not self.cache:
            return None
            
        results = []
        for prompt in prompts:
            cache_key = hash(prompt)
            # Fetch from layer_idx=0, position derived from hash
            cached = self.cache.get(0, cache_key % 1000, str(cache_key))
            if cached:
                results.append(cached.decode('utf-8'))
            else:
                return None
        return results
        
    def update_cache(self, prompts: List[str], results: List[str]):
        if not self.cache:
            return
            
        try:
            for prompt, result in zip(prompts, results):
                cache_key = hash(prompt)
                cache_data = (prompt + result).encode('utf-8')
                self.cache.put(
                    layer_idx=0,
                    position=cache_key % 1000,
                    data=cache_data,
                    key=str(cache_key),
                )
        except Exception as e:
            logger.debug(f"Cache update failed: {e}")

# Global singleton
engine_cache = EngineCacheMiddleware()
