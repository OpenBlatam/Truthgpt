"""
Circuit Breaker Resilience Pattern for Optimization Core.
=========================================================
Provides fault-tolerance, failure rate threshold monitoring, and automatic
service degradation / recovery context managers and decorators.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type
from pydantic import BaseModel, ConfigDict

try:
    from .exceptions import CircuitBreakerOpenError
    from .interfaces import BaseResilienceHandler
    from .types import CircuitBreakerConfig, CircuitState
except (ImportError, ValueError):
    try:
        from exceptions import CircuitBreakerOpenError
        from interfaces import BaseResilienceHandler
        from types import CircuitBreakerConfig, CircuitState
    except (ImportError, ValueError):
        from utils.exceptions import CircuitBreakerOpenError
        from utils.interfaces import BaseResilienceHandler
        from utils.types import CircuitBreakerConfig, CircuitState


logger = logging.getLogger(__name__)


class CircuitBreaker(BaseResilienceHandler):
    """Circuit breaker implementation with state transition tracking and automatic recovery."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None, **kwargs: Any) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker identifier
            config: Optional CircuitBreakerConfig instance or configuration kwargs
        """
        if config is None:
            self.config = CircuitBreakerConfig(**kwargs) if kwargs else CircuitBreakerConfig()
        else:
            self.config = config

        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize circuit breaker."""
        self.reset()

    def shutdown(self) -> None:
        """Reset state on shutdown."""
        self.reset()

    def health_check(self) -> Dict[str, Any]:
        """Perform diagnostic health check."""
        return {
            "status": "healthy" if self.state != CircuitState.OPEN else "degraded",
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Return component metadata."""
        return {
            "name": self.name,
            "category": "resilience",
            "type": "CircuitBreaker",
        }

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Call function through circuit breaker protection.

        Args:
            func: Target callable
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of func call
        """
        self._check_state_transition()

        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_state_change
            remaining = max(0.0, self.config.timeout - elapsed)
            raise CircuitBreakerOpenError(
                breaker_name=self.name,
                failure_count=self.failure_count,
                cooldown_remaining=remaining,
            )

        try:
            result = func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            else:
                self.failure_count = 0

            return result

        except self.config.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()

            raise

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Alias for BaseResilienceHandler interface."""
        return self.call(func, *args, **kwargs)

    def _check_state_transition(self) -> None:
        """Check if circuit should transition from OPEN to HALF_OPEN."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_state_change >= self.config.timeout:
                self._transition_to_half_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN (failures: {self.failure_count})")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.success_count = 0

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.failure_count = 0
        self.success_count = 0

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.failure_count = 0
        self.success_count = 0

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        self._transition_to_closed()

    def get_state(self) -> Dict[str, Any]:
        """Get current state dictionary."""
        return {
            "name": self.name,
            "state": self.state.value if isinstance(self.state, Enum) else str(self.state),
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0,
    expected_exception: type = Exception,
) -> Callable[..., Any]:
    """Decorator to wrap functions in a circuit breaker pattern."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout,
        expected_exception=expected_exception,
    )
    breaker = CircuitBreaker(name, config)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        wrapper.circuit_breaker = breaker  # type: ignore[attr-defined]
        return wrapper

    return decorator


__all__ = [
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "circuit_breaker",
]
