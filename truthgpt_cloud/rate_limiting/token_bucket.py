"""
⏱️ TruthGPT Cloud - Token Bucket Rate Limiter
Provides thread-safe token bucket rate limiting with automatic refill,
burst tolerance, and tier-based quota enforcement.
"""

import time
import threading
from typing import Dict, Tuple, Optional, Union

from ..core.tiers import CloudTier, get_tier_config
from ..core.exceptions import (
    RateLimitExceededError,
    QuotaExceededError,
)


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter supporting requests-per-minute (RPM) and burst limits.
    Thread-safe implementation with automatic token refilling.
    """

    def __init__(self):
        self._lock = threading.RLock()
        # user_id -> (current_tokens, last_updated_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = {}

    def check_rate_limit(self, user_id: str, tier: Union[str, CloudTier], cost: float = 1.0) -> bool:
        """
        Verify if request is permitted under user's tier RPM capacity.
        Raises QuotaExceededError if rate limit is exceeded.
        """
        config = get_tier_config(tier)
        capacity = float(config.requests_per_minute)
        refill_rate = capacity / 60.0  # tokens per second
        now = time.time()

        with self._lock:
            if user_id not in self._buckets:
                self._buckets[user_id] = (capacity, now)

            current_tokens, last_time = self._buckets[user_id]

            # Refill tokens based on elapsed time
            elapsed = max(0.0, now - last_time)
            current_tokens = min(capacity, current_tokens + elapsed * refill_rate)

            if current_tokens >= cost:
                self._buckets[user_id] = (current_tokens - cost, now)
                return True
            else:
                retry_after = max(0.1, round((cost - current_tokens) / max(0.01, refill_rate), 2))
                raise QuotaExceededError(
                    message=f"Límite de velocidad (RPM) excedido para el plan {config.tier_id.value.upper()}. Reintente en {retry_after}s.",
                    limit=int(capacity),
                    consumed=int(capacity - current_tokens),
                )

    def check_and_consume(self, user_id: str, rpm_capacity: int = 15, cost: float = 1.0) -> bool:
        """
        Check if user bucket has enough tokens and consume `cost`.
        Raises RateLimitExceededError if bucket is empty.
        """
        now = time.time()
        with self._lock:
            if user_id not in self._buckets:
                self._buckets[user_id] = (float(rpm_capacity), now)

            current_tokens, last_time = self._buckets[user_id]
            elapsed = max(0.0, now - last_time)
            refill_rate = float(rpm_capacity) / 60.0
            current_tokens = min(float(rpm_capacity), current_tokens + elapsed * refill_rate)

            if current_tokens >= cost:
                self._buckets[user_id] = (current_tokens - cost, now)
                return True
            else:
                retry_after = max(0.5, round((cost - current_tokens) / max(0.01, refill_rate), 1))
                raise RateLimitExceededError(
                    message=f"Límite de {rpm_capacity} peticiones por minuto superado.",
                    retry_after_seconds=retry_after,
                )

    def reset_user(self, user_id: str) -> None:
        """Reset rate limiter bucket for a user."""
        with self._lock:
            if user_id in self._buckets:
                del self._buckets[user_id]

    def get_user_tokens(self, user_id: str, max_capacity: float = 15.0) -> float:
        """Get current estimated token balance in bucket."""
        with self._lock:
            if user_id not in self._buckets:
                return max_capacity
            tokens, last_time = self._buckets[user_id]
            elapsed = max(0.0, time.time() - last_time)
            return min(max_capacity, tokens + elapsed * (max_capacity / 60.0))


# Module singleton instance
token_bucket_limiter = TokenBucketRateLimiter()

__all__ = [
    "TokenBucketRateLimiter",
    "token_bucket_limiter",
]
