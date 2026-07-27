import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from optimization_core.polyglot.kv_cache import KVCache
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False

class PolyglotCacheManager:
    """Manages the Rust KV cache for polyglot engine integration."""
    
    def __init__(self, use_rust_kv_cache: bool = True):
        self.external_cache = None
        if use_rust_kv_cache and POLYGLOT_AVAILABLE:
            try:
                self.external_cache = KVCache(
                    max_size=16384,
                    eviction_strategy="adaptive",
                    enable_compression=True,
                )
                logger.info("External Rust KV cache initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize external Rust KV cache: {e}")

    def get_from_cache(self, prompts: List[str]) -> Optional[List[str]]:
        """Attempt to retrieve results from cache."""
        if not self.external_cache:
            return None
        
        results = []
        for prompt in prompts:
            cache_key = hash(prompt)
            cached = self.external_cache.get(0, cache_key % 1000, str(cache_key))
            if cached:
                results.append(cached.decode('utf-8'))
            else:
                # Require all prompts in batch to be cached, otherwise miss
                return None
        
        return results

    def update_cache(self, prompts: List[str], results: List[str]):
        """Store results into cache."""
        if not self.external_cache:
            return
        
        try:
            for prompt, result in zip(prompts, results):
                cache_key = hash(prompt)
                cache_data = (prompt + result).encode('utf-8')
                self.external_cache.put(
                    layer_idx=0,
                    position=cache_key % 1000,
                    data=cache_data,
                    key=str(cache_key),
                )
        except Exception as e:
            logger.debug(f"Cache update failed: {e}")

    def get_stats(self) -> dict:
        if self.external_cache:
            return self.external_cache.stats()
        return {"status": "unavailable"}
