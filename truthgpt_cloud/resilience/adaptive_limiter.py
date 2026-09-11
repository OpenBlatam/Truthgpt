"""
⚖️ TruthGPT Cloud - Adaptive Concurrency Limiter
Dynamic concurrency control based on Little's Law (L = λW) and latency gradient tracking (TCP Vegas).
Prevents SMT solver overload collapse by dynamically adjusting in-flight concurrency windows based on observed RTT.
"""

import time
import asyncio
import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("TruthGPT.AdaptiveConcurrencyLimiter")


from ..core.exceptions import ConcurrencyLimitExceededError


class ConcurrencyLimitExceeded(ConcurrencyLimitExceededError):
    """Raised when in-flight capacity is exhausted and acquire times out."""
    def __init__(self, name: str, current_limit: int, in_flight: int):
        self.name = name
        self.current_limit = current_limit
        self.in_flight = in_flight
        super().__init__(
            f"Concurrency limit exceeded for '{name}': "
            f"{in_flight}/{current_limit} slots currently occupied."
        )


class AdaptiveConcurrencyLimiter:
    """
    Thread-safe and asyncio-compatible Adaptive Concurrency Limiter.

    Calculates optimal concurrency limits based on:
    - Little's Law: Concurrency = Throughput * Latency (L = λ * W)
    - Gradient algorithm (Vegas): gradient = min_rtt / smoothed_rtt
      - If gradient >= 1.0 (no queueing / fast response): current_limit += headroom
      - If gradient < 1.0 (queueing detected): current_limit = current_limit * gradient
      - On failure/timeout: multiplicative backoff (current_limit *= backoff_ratio)

    Supports both sync (`with limiter:`) and async (`async with limiter:`) contexts.
    """

    def __init__(
        self,
        name: str = "default_limiter",
        initial_limit: int = 16,
        min_limit: int = 2,
        max_limit: int = 128,
        smoothing_factor: float = 0.2,
        headroom: float = 1.0,
        backoff_ratio: float = 0.8,
        default_timeout: float = 0.05,
    ):
        self.name = name
        self.initial_limit = max(min_limit, min(max_limit, initial_limit))
        self.current_limit: float = float(self.initial_limit)
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.smoothing_factor = smoothing_factor
        self.headroom = headroom
        self.backoff_ratio = backoff_ratio
        self.default_timeout = default_timeout

        self._in_flight: int = 0
        self._min_rtt_ms: float = float("inf")
        self._smoothed_rtt_ms: float = 0.0
        self._total_requests: int = 0
        self._successful_requests: int = 0
        self._failed_requests: int = 0
        self._rejected_requests: int = 0

        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._async_lock = asyncio.Lock()

    @property
    def in_flight(self) -> int:
        with self._lock:
            return self._in_flight

    @property
    def limit(self) -> int:
        with self._lock:
            return int(round(self.current_limit))

    def try_acquire(self) -> bool:
        """
        Non-blocking attempt to acquire a concurrency slot.
        Returns True if a slot was acquired, False if capacity is full.
        """
        with self._condition:
            if self._in_flight < int(round(self.current_limit)):
                self._in_flight += 1
                self._total_requests += 1
                return True
            return False

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Synchronously acquire a concurrency slot.
        Blocks until a slot is available or timeout expires.
        """
        to = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + to

        with self._condition:
            while self._in_flight >= int(round(self.current_limit)):
                remaining = deadline - time.time()
                if remaining <= 0:
                    self._rejected_requests += 1
                    raise ConcurrencyLimitExceeded(
                        self.name, int(round(self.current_limit)), self._in_flight
                    )
                self._condition.wait(timeout=max(0.001, remaining))

            self._in_flight += 1
            self._total_requests += 1
            return True

    def try_acquire(self) -> bool:
        """
        Attempt to immediately acquire a concurrency slot without blocking.
        Returns True if acquired, False otherwise.
        """
        with self._condition:
            if self._in_flight < int(round(self.current_limit)):
                self._in_flight += 1
                self._total_requests += 1
                return True
            return False

    def release(self, latency_ms: float, success: bool = True):
        """
        Release a slot and adapt the concurrency limit based on measured RTT latency and success status.
        """
        with self._condition:
            if self._in_flight > 0:
                self._in_flight -= 1

            if success:
                self._successful_requests += 1
                if latency_ms < self._min_rtt_ms:
                    self._min_rtt_ms = latency_ms

                if self._smoothed_rtt_ms == 0.0:
                    self._smoothed_rtt_ms = latency_ms
                else:
                    self._smoothed_rtt_ms = (
                        (1.0 - self.smoothing_factor) * self._smoothed_rtt_ms
                        + self.smoothing_factor * latency_ms
                    )

                # Vegas gradient calculation
                gradient = (
                    self._min_rtt_ms / max(self._smoothed_rtt_ms, 1e-4)
                    if self._smoothed_rtt_ms > 0
                    else 1.0
                )

                if gradient >= 0.95:
                    # Healthy headroom growth
                    new_limit = self.current_limit + self.headroom
                else:
                    # Queue delay detected: adjust downwards proportionally
                    new_limit = self.current_limit * gradient

                self.current_limit = max(
                    float(self.min_limit), min(float(self.max_limit), new_limit)
                )
            else:
                self._failed_requests += 1
                # Multiplicative decrease on failure
                new_limit = self.current_limit * self.backoff_ratio
                self.current_limit = max(
                    float(self.min_limit), min(float(self.max_limit), new_limit)
                )

            self._condition.notify_all()

    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """
        Asynchronously acquire a slot.
        """
        to = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + to

        while True:
            with self._lock:
                if self._in_flight < int(round(self.current_limit)):
                    self._in_flight += 1
                    self._total_requests += 1
                    return True

            if time.time() >= deadline:
                with self._lock:
                    self._rejected_requests += 1
                raise ConcurrencyLimitExceeded(
                    self.name, int(round(self.current_limit)), self.in_flight
                )

            await asyncio.sleep(0.01)

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive telemetry and diagnostic metrics."""
        with self._lock:
            cur_limit = int(round(self.current_limit))
            utilization = (
                round((self._in_flight / max(cur_limit, 1)) * 100.0, 1)
            )
            min_rtt = round(self._min_rtt_ms, 2) if self._min_rtt_ms != float("inf") else 0.0
            return {
                "name": self.name,
                "limit": cur_limit,
                "current_limit": cur_limit,
                "min_limit": self.min_limit,
                "max_limit": self.max_limit,
                "in_flight": self._in_flight,
                "utilization_percent": utilization,
                "min_rtt_ms": min_rtt,
                "smoothed_rtt_ms": round(self._smoothed_rtt_ms, 2),
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "rejected_requests": self._rejected_requests,
            }

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic statistics compatible with get_stats contract."""
        return self.get_status()

    def reset(self):
        """Reset limiter state to initial parameters."""
        with self._condition:
            self.current_limit = float(self.initial_limit)
            self._in_flight = 0
            self._min_rtt_ms = float("inf")
            self._smoothed_rtt_ms = 0.0
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._rejected_requests = 0
            self._condition.notify_all()

    # Synchronous Context Manager
    def __enter__(self):
        self._start_time = time.perf_counter()
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.perf_counter() - getattr(self, "_start_time", time.perf_counter())) * 1000.0
        success = exc_type is None
        if latency_ms >= 1.0:
            self.release(latency_ms=latency_ms, success=success)
        else:
            with self._condition:
                if self._in_flight > 0:
                    self._in_flight -= 1
                self._condition.notify_all()

    # Asynchronous Context Manager
    async def __aenter__(self):
        self._async_start_time = time.perf_counter()
        await self.acquire_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.perf_counter() - getattr(self, "_async_start_time", time.perf_counter())) * 1000.0
        success = exc_type is None
        if latency_ms >= 1.0:
            self.release(latency_ms=latency_ms, success=success)
        else:
            with self._condition:
                if self._in_flight > 0:
                    self._in_flight -= 1
                self._condition.notify_all()


# Global singleton instance
adaptive_concurrency_limiter = AdaptiveConcurrencyLimiter(
    name="truthgpt_cloud_smt_limiter",
    initial_limit=16,
    min_limit=2,
    max_limit=128
)

__all__ = [
    "AdaptiveConcurrencyLimiter",
    "ConcurrencyLimitExceeded",
    "ConcurrencyLimitExceededError",
    "adaptive_concurrency_limiter",
]
