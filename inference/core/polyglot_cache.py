"""
High-Performance Polyglot Cache Manager for KV Cache Optimization.
"""

import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from optimization_core.polyglot.kv_cache import KVCache
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False


try:
    from optimization_core.inference.monitoring.metrics import metrics_collector
except Exception:
    metrics_collector = None


class PolyglotCacheManager:
    """Manages the Rust KV cache and Python fallback memory for polyglot engine integration."""

    def __init__(self, use_rust_kv_cache: bool = True, max_size: int = 16384):
        self.external_cache = None
        self.hits = 0
        self.misses = 0
        self._fallback_cache: Dict[str, str] = {}
        self._lock = threading.Lock()

        if use_rust_kv_cache and POLYGLOT_AVAILABLE:
            try:
                self.external_cache = KVCache(
                    max_size=max_size,
                    eviction_strategy="adaptive",
                    enable_compression=True,
                )
                logger.info("External Rust KV cache initialized successfully (max_size=%d).", max_size)
            except Exception as e:
                logger.warning(f"Failed to initialize external Rust KV cache: {e}")

    def get_from_cache(self, prompts: List[str]) -> Optional[List[str]]:
        """Attempt to retrieve cached inference results for a list of prompts."""
        with self._lock:
            if not self.external_cache:
                # Check python fallback cache
                results = []
                for prompt in prompts:
                    val = self._fallback_cache.get(prompt)
                    if val is None:
                        self.misses += len(prompts)
                        if metrics_collector:
                            metrics_collector.increment("inference_cache_misses_total", value=len(prompts))
                        return None
                    results.append(val)
                self.hits += len(prompts)
                if metrics_collector:
                    metrics_collector.increment("inference_cache_hits_total", value=len(prompts))
                return results

            results = []
            for prompt in prompts:
                cache_key = hash(prompt)
                cached = self.external_cache.get(0, cache_key % 1000, str(cache_key))
                if cached:
                    results.append(cached.decode('utf-8'))
                else:
                    self.misses += len(prompts)
                    if metrics_collector:
                        metrics_collector.increment("inference_cache_misses_total", value=len(prompts))
                    return None

            self.hits += len(prompts)
            if metrics_collector:
                metrics_collector.increment("inference_cache_hits_total", value=len(prompts))
            return results

    def update_cache(self, prompts: List[str], results: List[str]) -> None:
        """Store inference results into Rust KV cache or Python fallback."""
        with self._lock:
            if not self.external_cache:
                for prompt, result in zip(prompts, results):
                    self._fallback_cache[prompt] = result
                return

            try:
                for prompt, result in zip(prompts, results):
                    cache_key = hash(prompt)
                    cache_data = result.encode('utf-8')
                    self.external_cache.put(
                        layer_idx=0,
                        position=cache_key % 1000,
                        data=cache_data,
                        key=str(cache_key),
                    )
            except Exception as e:
                logger.debug(f"Cache update failed: {e}")

    def clear(self) -> None:
        """Clear cached items."""
        with self._lock:
            self._fallback_cache.clear()
            self.hits = 0
            self.misses = 0

    def invalidate_keys(self, prompts: List[str]) -> None:
        """Remove specific prompts from in-memory fallback cache."""
        with self._lock:
            for p in prompts:
                self._fallback_cache.pop(p, None)

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
            stats = {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": round(hit_rate, 2),
            }
            if self.external_cache:
                try:
                    stats.update(self.external_cache.stats())
                except Exception:
                    pass
                stats["status"] = "active_rust"
            else:
                stats["status"] = "active_fallback"
                stats["fallback_size"] = len(self._fallback_cache)
            return stats


__all__ = [
    "PolyglotCacheManager",
    "POLYGLOT_AVAILABLE",
]
