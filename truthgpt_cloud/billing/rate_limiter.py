"""
⏱️ TruthGPT Cloud - Rate Limiting & Concurrency Manager
Provides Sliding-Window & Token Bucket Requests-Per-Minute (RPM) enforcement and concurrency guards.
"""

import time
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
from ..core.exceptions import RateLimitExceededError, ConcurrencyLimitExceededError

RateLimitExceeded = RateLimitExceededError


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter for strict capacity and burst rate limit checking.
    """

    def __init__(self):
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}

    def check_and_consume(self, user_id: str, rpm_capacity: int = 15, cost: float = 1.0) -> bool:
        """
        Check if user bucket has enough tokens and consume `cost`.
        Raises RateLimitExceededError if bucket is empty.
        """
        now = time.time()
        if user_id not in self._tokens:
            self._tokens[user_id] = float(rpm_capacity)
            self._last_update[user_id] = now
            
        elapsed = now - self._last_update[user_id]
        self._last_update[user_id] = now
        
        # Refill tokens according to RPM rate (rpm_capacity tokens per 60 seconds)
        refill_rate = float(rpm_capacity) / 60.0
        self._tokens[user_id] = min(float(rpm_capacity), self._tokens[user_id] + (elapsed * refill_rate))
        
        if self._tokens[user_id] >= cost:
            self._tokens[user_id] -= cost
            return True
        else:
            raise RateLimitExceededError(
                message=f"Límite de {rpm_capacity} peticiones por minuto superado.",
                retry_after_seconds=max(0.5, round((cost - self._tokens[user_id]) / max(0.01, refill_rate), 1))
            )


class SlidingWindowRateLimiter:
    """
    Thread-safe / Async-safe sliding window rate limiter for TruthGPT Cloud tiers.
    """

    def __init__(self):
        self._request_history: Dict[str, List[float]] = defaultdict(list)
        self._active_concurrency: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: str, max_rpm: int) -> bool:
        """
        Check if user is within RPM limit.
        Raises RateLimitExceededError if limit is breached.
        """
        now = time.time()
        window_start = now - 60.0
        
        async with self._lock:
            # Purge entries older than 60 seconds
            self._request_history[user_id] = [
                ts for ts in self._request_history[user_id] if ts > window_start
            ]
            
            if len(self._request_history[user_id]) >= max_rpm:
                oldest = self._request_history[user_id][0]
                retry_after = max(0.5, round(60.0 - (now - oldest), 1))
                raise RateLimitExceededError(
                    message=f"Límite de {max_rpm} peticiones por minuto (RPM) alcanzado para su nivel.",
                    retry_after_seconds=retry_after
                )
            
            self._request_history[user_id].append(now)
            return True

    def acquire_concurrency(self, user_id: str, max_concurrent: int) -> bool:
        """Acquire a concurrent execution slot."""
        if self._active_concurrency[user_id] >= max_concurrent:
            raise ConcurrencyLimitExceededError(
                message=f"Límite de {max_concurrent} peticiones simultáneas alcanzado.",
                max_concurrent=max_concurrent
            )
        self._active_concurrency[user_id] += 1
        return True

    def release_concurrency(self, user_id: str) -> None:
        """Release a concurrent execution slot."""
        if self._active_concurrency[user_id] > 0:
            self._active_concurrency[user_id] -= 1


# Global singleton instances
rate_limiter = SlidingWindowRateLimiter()
token_bucket_limiter = TokenBucketRateLimiter()
