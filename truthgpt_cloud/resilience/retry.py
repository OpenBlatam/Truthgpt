"""
🔄 TruthGPT Cloud - Retry with Exponential Backoff & Jitter
Configurable retry decorator for transient failure recovery.
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Tuple, Type, Optional, Any

logger = logging.getLogger("TruthGPT.Retry")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()

    def compute_delay(self, attempt: int) -> float:
        """Compute delay with exponential backoff and optional jitter."""
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator that retries a function with exponential backoff and jitter.

    Works with both sync and async functions.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds before first retry.
        max_delay: Maximum delay cap in seconds.
        retryable_exceptions: Tuple of exception types that trigger retry.
        non_retryable_exceptions: Tuple of exception types that should never be retried.
        on_retry: Optional callback invoked on each retry (attempt_number, exception).

    Usage:
        @retry_with_backoff(max_retries=3, retryable_exceptions=(ConnectionError, TimeoutError))
        async def call_external_api():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay_seconds=base_delay,
        max_delay_seconds=max_delay,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.non_retryable_exceptions:
                    raise
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt >= config.max_retries:
                        logger.warning(
                            f"Retry exhausted for {func.__name__} after {attempt + 1} attempts: {e}"
                        )
                        raise
                    delay = config.compute_delay(attempt)
                    logger.info(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"in {delay:.2f}s due to: {type(e).__name__}: {e}"
                    )
                    if on_retry:
                        on_retry(attempt + 1, e)
                    await asyncio.sleep(delay)
            raise last_exception  # Should not reach here

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.non_retryable_exceptions:
                    raise
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt >= config.max_retries:
                        logger.warning(
                            f"Retry exhausted for {func.__name__} after {attempt + 1} attempts: {e}"
                        )
                        raise
                    delay = config.compute_delay(attempt)
                    logger.info(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"in {delay:.2f}s due to: {type(e).__name__}: {e}"
                    )
                    if on_retry:
                        on_retry(attempt + 1, e)
                    time.sleep(delay)
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


__all__ = [
    "RetryConfig",
    "retry_with_backoff",
]
