"""
⏱️ TruthGPT Cloud - Sliding Window Rate Limiter & Concurrency Controller
Enforces Requests Per Minute (RPM), Tokens Per Minute (TPM), and concurrency limits by tier.
"""

import time
import threading
from collections import deque
from typing import Dict, Deque, Tuple, Optional
from .exceptions import RateLimitExceededError


class SlidingWindowRateLimiter:
    """
    In-memory Sliding Window Log Rate Limiter.
    Tracks timestamps of requests within a moving 60-second window.
    """

    def __init__(self, window_size_seconds: float = 60.0):
        self.window_size = window_size_seconds
        self._lock = threading.RLock()
        # user_id -> deque of timestamps
        self._request_windows: Dict[str, Deque[float]] = {}
        # user_id -> deque of (timestamp, token_count)
        self._token_windows: Dict[str, Deque[Tuple[float, int]]] = {}
        # user_id -> current concurrent request count
        self._concurrency_counts: Dict[str, int] = {}

    def check_and_record(
        self,
        user_id: str,
        max_rpm: int,
        estimated_tokens: int = 100,
        max_tpm: Optional[int] = None,
        max_concurrency: Optional[int] = None
    ) -> bool:
        """
        Check if the request passes the sliding window limits and record it.
        Raises RateLimitExceededError if limit is breached.
        """
        now = time.time()
        window_start = now - self.window_size

        with self._lock:
            # 1. Initialize user deques if absent
            if user_id not in self._request_windows:
                self._request_windows[user_id] = deque()
            if user_id not in self._token_windows:
                self._token_windows[user_id] = deque()

            req_deque = self._request_windows[user_id]
            tok_deque = self._token_windows[user_id]

            # 2. Evict expired entries outside window
            while req_deque and req_deque[0] < window_start:
                req_deque.popleft()
            while tok_deque and tok_deque[0][0] < window_start:
                tok_deque.popleft()

            # 3. Check Concurrency if configured
            if max_concurrency is not None:
                current_active = self._concurrency_counts.get(user_id, 0)
                if current_active >= max_concurrency:
                    raise RateLimitExceededError(
                        f"Concurrency limit ({max_concurrency} parallel requests) reached. Please wait for previous tasks to finish.",
                        retry_after_seconds=1.0
                    )

            # 4. Check Requests Per Minute (RPM)
            if len(req_deque) >= max_rpm:
                oldest_timestamp = req_deque[0]
                retry_after = max(0.1, round(self.window_size - (now - oldest_timestamp), 2))
                raise RateLimitExceededError(
                    f"Rate limit of {max_rpm} requests/min exceeded for your tier. Retry in {retry_after}s.",
                    retry_after_seconds=retry_after
                )

            # 5. Check Tokens Per Minute (TPM) if specified
            if max_tpm is not None:
                current_tokens_in_window = sum(t[1] for t in tok_deque)
                if current_tokens_in_window + estimated_tokens > max_tpm:
                    raise RateLimitExceededError(
                        f"Token rate limit of {max_tpm} TPM exceeded. Retry shortly.",
                        retry_after_seconds=2.0
                    )

            # 6. Record usage in sliding window
            req_deque.append(now)
            tok_deque.append((now, estimated_tokens))
            return True

    def acquire_concurrency(self, user_id: str) -> None:
        with self._lock:
            self._concurrency_counts[user_id] = self._concurrency_counts.get(user_id, 0) + 1

    def release_concurrency(self, user_id: str) -> None:
        with self._lock:
            current = self._concurrency_counts.get(user_id, 0)
            if current > 0:
                self._concurrency_counts[user_id] = current - 1

    def get_user_rate_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get live RPM and TPM stats for a user."""
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
                "active_concurrent_requests": active_concurrent
            }


# Global Singleton Rate Limiter
cloud_rate_limiter = SlidingWindowRateLimiter()
