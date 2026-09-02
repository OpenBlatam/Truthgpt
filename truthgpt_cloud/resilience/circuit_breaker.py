"""
⚡ TruthGPT Cloud - Circuit Breaker Pattern
Thread-safe implementation with CLOSED → OPEN → HALF_OPEN state machine.
Protects downstream services from cascading failures.
"""

import time
import threading
import logging
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger("TruthGPT.CircuitBreaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is in OPEN state and rejects calls."""
    def __init__(self, name: str, recovery_time_remaining: float):
        self.name = name
        self.recovery_time_remaining = recovery_time_remaining
        super().__init__(
            f"Circuit breaker '{name}' is OPEN. "
            f"Retry in {recovery_time_remaining:.1f}s."
        )


@dataclass
class CircuitBreakerMetrics:
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_rejections: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float = 0.0
    last_state_change_time: float = 0.0


class CircuitBreaker:
    """
    Thread-safe Circuit Breaker with configurable thresholds.

    States:
    - CLOSED: Normal operation. Failures are counted.
    - OPEN: Calls are rejected. After recovery_timeout, transitions to HALF_OPEN.
    - HALF_OPEN: Limited calls allowed. If they succeed, transitions to CLOSED.

    Usage:
        cb = CircuitBreaker("inference_router", failure_threshold=5)
        with cb:
            result = await some_external_call()
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        success_threshold: int = 2,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._metrics = CircuitBreakerMetrics()
        self._half_open_calls = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._opened_at >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        with self._lock:
            return CircuitBreakerMetrics(
                total_calls=self._metrics.total_calls,
                total_successes=self._metrics.total_successes,
                total_failures=self._metrics.total_failures,
                total_rejections=self._metrics.total_rejections,
                consecutive_failures=self._metrics.consecutive_failures,
                consecutive_successes=self._metrics.consecutive_successes,
                last_failure_time=self._metrics.last_failure_time,
                last_state_change_time=self._metrics.last_state_change_time,
            )

    def _transition_to(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        self._metrics.last_state_change_time = time.time()

        if new_state == CircuitState.OPEN:
            self._opened_at = time.time()
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        elif new_state == CircuitState.CLOSED:
            self._metrics.consecutive_failures = 0

        logger.info(
            f"CircuitBreaker '{self.name}': {old_state.value} → {new_state.value}"
        )

    def _before_call(self) -> None:
        """Check state before executing a call."""
        with self._lock:
            current_state = self.state  # triggers auto OPEN→HALF_OPEN check

            if current_state == CircuitState.OPEN:
                remaining = max(0.0, self.recovery_timeout - (time.time() - self._opened_at))
                self._metrics.total_rejections += 1
                raise CircuitBreakerOpen(self.name, remaining)

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._metrics.total_rejections += 1
                    raise CircuitBreakerOpen(self.name, 0.0)
                self._half_open_calls += 1

            self._metrics.total_calls += 1

    def _on_success(self) -> None:
        """Record successful call."""
        with self._lock:
            self._metrics.total_successes += 1
            self._metrics.consecutive_failures = 0
            self._metrics.consecutive_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                if self._metrics.consecutive_successes >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def _on_failure(self, exc: Exception) -> None:
        """Record failed call."""
        with self._lock:
            self._metrics.total_failures += 1
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            self._metrics.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._metrics.consecutive_failures >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def __enter__(self):
        self._before_call()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._on_success()
        else:
            if exc_type is not CircuitBreakerOpen:
                self._on_failure(exc_val)
        return False

    async def __aenter__(self):
        self._before_call()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._on_success()
        else:
            if exc_type is not CircuitBreakerOpen:
                self._on_failure(exc_val)
        return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function within the circuit breaker."""
        self._before_call()
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def reset(self) -> None:
        """Force reset to CLOSED state (for testing / admin)."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._metrics = CircuitBreakerMetrics()

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout,
                "metrics": {
                    "total_calls": self._metrics.total_calls,
                    "total_successes": self._metrics.total_successes,
                    "total_failures": self._metrics.total_failures,
                    "total_rejections": self._metrics.total_rejections,
                    "consecutive_failures": self._metrics.consecutive_failures,
                    "consecutive_successes": self._metrics.consecutive_successes,
                },
            }


__all__ = [
    "CircuitState",
    "CircuitBreakerOpen",
    "CircuitBreakerMetrics",
    "CircuitBreaker",
]
