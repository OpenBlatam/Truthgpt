"""
⏱️ TruthGPT Cloud - Sliding Window Rate Limiter & Concurrency Controller
Enforces Requests Per Minute (RPM), Tokens Per Minute (TPM), and concurrency limits by tier.
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
from ..core.interfaces import IRateLimiter

# Compatibility alias
RateLimitExceeded = RateLimitExceededError


class SlidingWindowRateLimiter(IRateLimiter):
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
        tier_or_rpm: Union[str, CloudTier, int, None] = 60,
        window_seconds: Optional[float] = None,
        tier: Optional[Any] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Check if user is within RPM limit (synchronous check with tier or explicit rpm).
        Raises RateLimitExceededError if limit is breached.
        """
        target_tier = tier if tier is not None else tier_or_rpm
        if target_tier is None:
            max_rpm = 60
        elif isinstance(target_tier, int):
            max_rpm = target_tier
        elif hasattr(target_tier, "requests_per_minute"):
            max_rpm = int(target_tier.requests_per_minute)
        else:
            config = get_tier_config(target_tier)
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

    def check_rate_limit(self, identifier: str, tier: Optional[Any] = None) -> bool:
        """Check whether the identifier is within allowable rate limits."""
        max_rpm = 60
        if tier is not None:
            cfg = get_tier_config(tier) if hasattr(tier, "value") or isinstance(tier, str) else tier
            if hasattr(cfg, "requests_per_minute"):
                max_rpm = cfg.requests_per_minute
        is_limited, _ = self.is_rate_limited(identifier, max_rpm=max_rpm)
        return not is_limited

    def consume(self, identifier: str, tokens: int = 1, tier: Optional[Any] = None) -> None:
        """Consume request or token budget against limits."""
        self.check_and_record(user_id=identifier, tier=tier, tokens=tokens)

    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset limits for an identifier or all tracked identifiers."""
        with self._lock:
            if identifier is None:
                self._request_windows.clear()
                self._token_windows.clear()
                self._concurrency_counts.clear()
            else:
                self.reset_user(identifier)


# Global singleton instances
cloud_rate_limiter = SlidingWindowRateLimiter()
rate_limiter = cloud_rate_limiter

__all__ = [
    "SlidingWindowRateLimiter",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "cloud_rate_limiter",
    "rate_limiter",
]
