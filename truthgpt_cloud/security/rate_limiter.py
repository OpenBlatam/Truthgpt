"""
⏱️ TruthGPT Cloud - Security & Rate Limiting Engine
Provides unified Token Bucket and Sliding Window rate limiting algorithms,
concurrency guards, and RPM/TPM quota enforcement.
"""

import time
import threading
from collections import deque, defaultdict
from typing import Dict, Deque, Tuple, Optional, Any, Union

from ..core.tiers import CloudTier, get_tier_config
from ..core.exceptions import (
    RateLimitExceededError,
    QuotaExceededError,
    ConcurrencyLimitExceededError,
)

# Compatibility alias
RateLimitExceeded = RateLimitExceededError


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


class SlidingWindowRateLimiter:
    """
    Thread-safe and Async-compatible Sliding Window Log Rate Limiter.
    Tracks timestamps of requests within a moving window (default 60 seconds).
    Enforces RPM, TPM, and Concurrency limits.
    """

    def __init__(self, window_size_seconds: float = 60.0):
        self.window_size = window_size_seconds
        self._lock = threading.RLock()
        # user_id -> deque of timestamps
        self._request_windows: Dict[str, Deque[float]] = {}
        # user_id -> deque of (timestamp, token_count)
        self._token_windows: Dict[str, Deque[Tuple[float, int]]] = {}
        # user_id -> current concurrent request count
        self._concurrency_counts: Dict[str, int] = defaultdict(int)

    def check_and_record(
        self,
        user_id: str,
        max_rpm: int,
        estimated_tokens: int = 100,
        max_tpm: Optional[int] = None,
        max_concurrency: Optional[int] = None,
    ) -> bool:
        """
        Check if the request passes the sliding window limits and record it synchronously.
        Raises RateLimitExceededError or ConcurrencyLimitExceededError if limit is breached.
        """
        now = time.time()
        window_start = now - self.window_size

        with self._lock:
            if user_id not in self._request_windows:
                self._request_windows[user_id] = deque()
            if user_id not in self._token_windows:
                self._token_windows[user_id] = deque()

            req_deque = self._request_windows[user_id]
            tok_deque = self._token_windows[user_id]

            # Evict expired entries outside window
            while req_deque and req_deque[0] < window_start:
                req_deque.popleft()
            while tok_deque and tok_deque[0][0] < window_start:
                tok_deque.popleft()

            # Concurrency check
            if max_concurrency is not None:
                current_active = self._concurrency_counts.get(user_id, 0)
                if current_active >= max_concurrency:
                    raise ConcurrencyLimitExceededError(
                        message=f"Concurrency limit ({max_concurrency} parallel requests) reached. Please wait for previous tasks to finish.",
                        max_concurrent=max_concurrency,
                    )

            # RPM check
            if len(req_deque) >= max_rpm:
                oldest_timestamp = req_deque[0]
                retry_after = max(0.1, round(self.window_size - (now - oldest_timestamp), 2))
                raise RateLimitExceededError(
                    message=f"Rate limit of {max_rpm} requests/min exceeded for your tier. Retry in {retry_after}s.",
                    retry_after_seconds=retry_after,
                )

            # TPM check
            if max_tpm is not None:
                current_tokens_in_window = sum(t[1] for t in tok_deque)
                if current_tokens_in_window + estimated_tokens > max_tpm:
                    raise RateLimitExceededError(
                        message=f"Token rate limit of {max_tpm} TPM exceeded. Retry shortly.",
                        retry_after_seconds=2.0,
                    )

            # Record usage
            req_deque.append(now)
            tok_deque.append((now, estimated_tokens))
            return True

    def check_rate_limit(
        self,
        user_id: str,
        tier_or_rpm: Union[str, CloudTier, int] = 60,
        window_seconds: Optional[float] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Check if user is within RPM limit (synchronous check with tier or explicit rpm).
        Raises RateLimitExceededError if limit is breached.
        """
        if isinstance(tier_or_rpm, int):
            max_rpm = tier_or_rpm
        else:
            config = get_tier_config(tier_or_rpm)
            max_rpm = int(config.requests_per_minute)

        now = time.time()
        w_size = window_seconds if window_seconds is not None else self.window_size
        window_start = now - w_size

        with self._lock:
            if user_id not in self._request_windows:
                self._request_windows[user_id] = deque()

            req_deque = self._request_windows[user_id]
            while req_deque and req_deque[0] < window_start:
                req_deque.popleft()

            if len(req_deque) >= max_rpm:
                oldest = req_deque[0]
                retry_after = max(0.5, round(w_size - (now - oldest), 1))
                raise RateLimitExceededError(
                    message=f"Límite de {max_rpm} peticiones por minuto (RPM) alcanzado para su nivel.",
                    retry_after_seconds=retry_after,
                )

            req_deque.append(now)
            return True

    async def async_check_rate_limit(self, user_id: str, max_rpm: int) -> bool:
        """Asynchronous check if user is within RPM limit."""
        return self.check_rate_limit(user_id, max_rpm)

    def get_user_tokens(self, user_id: str, max_capacity: float = 60.0) -> float:
        """Get current remaining request quota or token capacity in active window."""
        now = time.time()
        window_start = now - self.window_size
        with self._lock:
            if user_id not in self._request_windows:
                return float(max_capacity)
            req_deque = self._request_windows[user_id]
            while req_deque and req_deque[0] < window_start:
                req_deque.popleft()
            return float(max(0.0, max_capacity - len(req_deque)))

    def acquire_concurrency(self, user_id: str, max_concurrent: Optional[int] = None) -> bool:
        """Acquire a concurrent execution slot."""
        with self._lock:
            current = self._concurrency_counts[user_id]
            if max_concurrent is not None and current >= max_concurrent:
                raise ConcurrencyLimitExceededError(
                    message=f"Límite de {max_concurrent} peticiones simultáneas alcanzado.",
                    max_concurrent=max_concurrent,
                )
            self._concurrency_counts[user_id] = current + 1
            return True

    def release_concurrency(self, user_id: str) -> None:
        """Release a concurrent execution slot."""
        with self._lock:
            current = self._concurrency_counts.get(user_id, 0)
            if current > 0:
                self._concurrency_counts[user_id] = current - 1

    def get_user_rate_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get live RPM, TPM, and active concurrency stats for a user."""
        now = time.time()
        window_start = now - self.window_size
        with self._lock:
            req_deque = self._request_windows.get(user_id, deque())
            tok_deque = self._token_windows.get(user_id, deque())

            valid_reqs = sum(1 for t in req_deque if t >= window_start)
            valid_tokens = sum(t[1] for t in tok_deque if t[0] >= window_start)
            active_concurrent = self._concurrency_counts.get(user_id, 0)

            return {
                "requests_last_minute": valid_reqs,
                "tokens_last_minute": valid_tokens,
                "active_concurrent_requests": active_concurrent,
                "window_size_seconds": self.window_size,
            }

    def limit(
        self,
        user_id: str,
        max_rpm: int = 60,
        max_concurrency: Optional[int] = None
    ):
        """Asynchronous context manager for rate limit and concurrency protection."""
        class _AsyncLimitCtx:
            def __init__(ctx_self):
                ctx_self.limiter = self
                ctx_self.user_id = user_id
                ctx_self.max_rpm = max_rpm
                ctx_self.max_concurrency = max_concurrency

            async def __aenter__(ctx_self):
                ctx_self.limiter.check_and_record(
                    ctx_self.user_id,
                    max_rpm=ctx_self.max_rpm,
                    max_concurrency=ctx_self.max_concurrency
                )
                ctx_self.limiter.acquire_concurrency(ctx_self.user_id, max_concurrent=ctx_self.max_concurrency)
                return ctx_self

            async def __aexit__(ctx_self, exc_type, exc_val, exc_tb):
                ctx_self.limiter.release_concurrency(ctx_self.user_id)
                return False

        return _AsyncLimitCtx()

    def sync_limit(
        self,
        user_id: str,
        max_rpm: int = 60,
        max_concurrency: Optional[int] = None
    ):
        """Synchronous context manager for rate limit and concurrency protection."""
        class _SyncLimitCtx:
            def __init__(ctx_self):
                ctx_self.limiter = self
                ctx_self.user_id = user_id
                ctx_self.max_rpm = max_rpm
                ctx_self.max_concurrency = max_concurrency

            def __enter__(ctx_self):
                ctx_self.limiter.check_and_record(
                    ctx_self.user_id,
                    max_rpm=ctx_self.max_rpm,
                    max_concurrency=ctx_self.max_concurrency
                )
                ctx_self.limiter.acquire_concurrency(ctx_self.user_id, max_concurrent=ctx_self.max_concurrency)
                return ctx_self

            def __exit__(ctx_self, exc_type, exc_val, exc_tb):
                ctx_self.limiter.release_concurrency(ctx_self.user_id)
                return False

        return _SyncLimitCtx()

    def is_rate_limited(self, user_id: str, max_rpm: int) -> Tuple[bool, float]:
        """
        Check whether a user would currently be rate-limited without recording a new request.
        Returns: (is_limited, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_size
        with self._lock:
            req_deque = self._request_windows.get(user_id, deque())
            valid_reqs = [t for t in req_deque if t >= window_start]
            if len(valid_reqs) >= max_rpm:
                oldest = valid_reqs[0]
                retry_after = max(0.1, round(self.window_size - (now - oldest), 2))
                return True, retry_after
            return False, 0.0

    def reset_user(self, user_id: str) -> None:
        """Reset rate limiter windows for a user."""
        with self._lock:
            if user_id in self._request_windows:
                del self._request_windows[user_id]
            if user_id in self._token_windows:
                del self._token_windows[user_id]
            if user_id in self._concurrency_counts:
                del self._concurrency_counts[user_id]


# Global singleton instances
cloud_rate_limiter = SlidingWindowRateLimiter()
token_bucket_limiter = TokenBucketRateLimiter()
rate_limiter = cloud_rate_limiter

__all__ = [
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    "cloud_rate_limiter",
    "token_bucket_limiter",
    "rate_limiter",
]
