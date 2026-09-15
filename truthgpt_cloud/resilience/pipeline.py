"""
🛡️ TruthGPT Cloud - Enterprise Unified Resilience Pipeline
Composes Rate Limiting, Adaptive Concurrency Gating, Circuit Breaking, and Exponential Backoff Retries
into a single, high-reliability execution pipeline for sync and async workflows.
"""

import time
import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Dict, TypeVar, Awaitable

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from .adaptive_limiter import AdaptiveConcurrencyLimiter, ConcurrencyLimitExceeded
from .retry import RetryConfig, retry_with_backoff
from ..core.exceptions import RateLimitExceededError, ConcurrencyLimitExceededError

logger = logging.getLogger("TruthGPT.ResiliencePipeline")

T = TypeVar("T")


@dataclass
class ResiliencePipelineMetrics:
    """Aggregated operational metrics for the resilience execution pipeline."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    rejected_by_rate_limiter: int = 0
    rejected_by_concurrency: int = 0
    rejected_by_circuit_breaker: int = 0
    retried_attempts: int = 0


class ResiliencePipeline:
    """
    Unified multi-layered resilience pipeline.
    Chains guards in priority order:
    1. Rate Limiter (RPM / TPM verification)
    2. Adaptive Concurrency Limiter (in-flight Vegas/AIMD slot allocation)
    3. Circuit Breaker (cascading failure suppression)
    4. Exponential Backoff Retry (transient error recovery with jitter)
    """

    def __init__(
        self,
        name: str = "resilience_pipeline",
        circuit_breaker: Optional[CircuitBreaker] = None,
        adaptive_limiter: Optional[AdaptiveConcurrencyLimiter] = None,
        rate_limiter: Optional[Any] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        self.name = name
        self.circuit_breaker = circuit_breaker or CircuitBreaker(name=f"{name}_cb")
        self.adaptive_limiter = adaptive_limiter or AdaptiveConcurrencyLimiter(name=f"{name}_acl")
        self.rate_limiter = rate_limiter
        self.retry_config = retry_config or RetryConfig(max_retries=2, base_delay_seconds=0.1)
        self.metrics = ResiliencePipelineMetrics()

    def check_rate_limit(self, user_id: str = "default") -> None:
        """Verify user rate limit before entering execution pipeline."""
        if self.rate_limiter is not None:
            allowed = True
            if hasattr(self.rate_limiter, "allow_request"):
                allowed = self.rate_limiter.allow_request(user_id)
            elif hasattr(self.rate_limiter, "check"):
                allowed = self.rate_limiter.check(user_id)
            if not allowed:
                self.metrics.rejected_by_rate_limiter += 1
                raise RateLimitExceededError(
                    f"Rate limit exceeded for user '{user_id}' under {self.name}."
                )

    def execute(
        self,
        fn: Callable[..., T],
        *args,
        user_id: str = "default",
        **kwargs
    ) -> T:
        """
        Synchronously execute callable through rate limiter, concurrency guard,
        circuit breaker, and retry engine.
        """
        self.metrics.total_executions += 1
        self.check_rate_limit(user_id=user_id)

        # Wrap in retry with backoff
        def _guarded_call():
            # Concurrency allocation
            with self.adaptive_limiter:
                # Circuit breaker check
                with self.circuit_breaker:
                    return fn(*args, **kwargs)

        try:
            # Execute with exponential backoff
            attempts = 0
            while True:
                try:
                    res = _guarded_call()
                    self.metrics.successful_executions += 1
                    return res
                except CircuitBreakerOpen:
                    self.metrics.rejected_by_circuit_breaker += 1
                    self.metrics.failed_executions += 1
                    raise
                except ConcurrencyLimitExceeded:
                    self.metrics.rejected_by_concurrency += 1
                    self.metrics.failed_executions += 1
                    raise
                except Exception as ex:
                    attempts += 1
                    if attempts > self.retry_config.max_retries:
                        self.metrics.failed_executions += 1
                        raise ex
                    self.metrics.retried_attempts += 1
                    delay = self.retry_config.compute_delay(attempts)
                    time.sleep(delay)
        except Exception:
            raise

    async def execute_async(
        self,
        fn: Callable[..., Awaitable[T]],
        *args,
        user_id: str = "default",
        **kwargs
    ) -> T:
        """
        Asynchronously execute coroutine through rate limiter, concurrency guard,
        circuit breaker, and retry engine.
        """
        self.metrics.total_executions += 1
        self.check_rate_limit(user_id=user_id)

        attempts = 0
        while True:
            try:
                # Concurrency slot
                async with self.adaptive_limiter:
                    with self.circuit_breaker:
                        res = await fn(*args, **kwargs)
                        self.metrics.successful_executions += 1
                        return res
            except CircuitBreakerOpen:
                self.metrics.rejected_by_circuit_breaker += 1
                self.metrics.failed_executions += 1
                raise
            except ConcurrencyLimitExceeded:
                self.metrics.rejected_by_concurrency += 1
                self.metrics.failed_executions += 1
                raise
            except Exception as ex:
                attempts += 1
                if attempts > self.retry_config.max_retries:
                    self.metrics.failed_executions += 1
                    raise ex
                self.metrics.retried_attempts += 1
                delay = self.retry_config.compute_delay(attempts)
                await asyncio.sleep(delay)

    def protect(self, user_id: str = "default"):
        """Decorator to wrap sync or async functions with the resilience pipeline."""
        def decorator(target_fn):
            if inspect.iscoroutinefunction(target_fn):
                async def async_wrapper(*args, **kwargs):
                    return await self.execute_async(target_fn, *args, user_id=user_id, **kwargs)
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    return self.execute(target_fn, *args, user_id=user_id, **kwargs)
                return sync_wrapper
        return decorator

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status and health of all chained resilience components."""
        return {
            "name": self.name,
            "circuit_breaker": self.circuit_breaker.get_status() if hasattr(self.circuit_breaker, "get_status") else {},
            "adaptive_limiter": self.adaptive_limiter.get_stats() if hasattr(self.adaptive_limiter, "get_stats") else {},
            "metrics": {
                "total_executions": self.metrics.total_executions,
                "successful_executions": self.metrics.successful_executions,
                "failed_executions": self.metrics.failed_executions,
                "rejected_by_rate_limiter": self.metrics.rejected_by_rate_limiter,
                "rejected_by_concurrency": self.metrics.rejected_by_concurrency,
                "rejected_by_circuit_breaker": self.metrics.rejected_by_circuit_breaker,
                "retried_attempts": self.metrics.retried_attempts,
            }
        }

    def reset(self) -> None:
        """Reset internal metrics and circuit states."""
        self.circuit_breaker.reset()
        self.adaptive_limiter.reset()
        self.metrics = ResiliencePipelineMetrics()


# Global default pipeline
resilience_pipeline = ResiliencePipeline()


def execute_with_resilience(fn: Callable[..., Any], *args, **kwargs) -> Any:
    """Helper function to run any callable with default resilience pipeline."""
    if inspect.iscoroutinefunction(fn):
        return resilience_pipeline.execute_async(fn, *args, **kwargs)
    return resilience_pipeline.execute(fn, *args, **kwargs)


__all__ = [
    "ResiliencePipeline",
    "ResiliencePipelineMetrics",
    "resilience_pipeline",
    "execute_with_resilience",
]
