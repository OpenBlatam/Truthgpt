"""
🔄 TruthGPT Cloud - Resilience & Enterprise Retry Engine
Powered by Tenacity with Exponential Backoff, Jitter, and Full Async/Sync Compatibility.
"""

import asyncio
import functools
import inspect
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Tuple, Type, Optional, Any, Union

logger = logging.getLogger("TruthGPT.Retry")

_HAS_TENACITY = False
try:
    import tenacity
    from tenacity import (
        Retrying,
        AsyncRetrying,
        stop_after_attempt,
        wait_exponential,
        wait_random_exponential,
        retry_if_exception_type,
        retry_if_not_exception_type,
        before_sleep_log,
        RetryError,
    )
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff & jitter."""
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
    Powered by Tenacity for enterprise-grade retry mechanics, with zero-dependency fallback.

    Works seamlessly with both synchronous and asynchronous functions.

    Args:
        max_retries: Maximum number of retry attempts (excluding the first run).
        base_delay: Base delay in seconds before first retry.
        max_delay: Maximum delay cap in seconds.
        retryable_exceptions: Tuple of exception types that trigger retry.
        non_retryable_exceptions: Tuple of exception types that should never be retried.
        on_retry: Optional callback invoked on each retry (attempt_number, exception).
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay_seconds=base_delay,
        max_delay_seconds=max_delay,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        if _HAS_TENACITY:
            def _build_retry_condition():
                condition = retry_if_exception_type(config.retryable_exceptions)
                if config.non_retryable_exceptions:
                    condition = condition & retry_if_not_exception_type(config.non_retryable_exceptions)
                return condition

            wait_strategy = (
                wait_random_exponential(multiplier=config.base_delay_seconds, max=config.max_delay_seconds)
                if config.jitter else
                wait_exponential(multiplier=config.base_delay_seconds, max=config.max_delay_seconds, exp_base=config.exponential_base)
            )

            def _tenacity_before_sleep(retry_state):
                attempt = retry_state.attempt_number
                exc = retry_state.outcome.exception() if retry_state.outcome else None
                logger.info(
                    f"[Tenacity] Retrying {func.__name__} (attempt {attempt}/{config.max_retries}) "
                    f"due to: {type(exc).__name__}: {exc}"
                )
                if on_retry and exc:
                    try:
                        on_retry(attempt, exc)
                    except Exception as cb_err:
                        logger.warning(f"Error in on_retry callback: {cb_err}")

            if is_async:
                @functools.wraps(func)
                async def async_tenacity_wrapper(*args, **kwargs) -> Any:
                    retryer = AsyncRetrying(
                        stop=stop_after_attempt(config.max_retries + 1),
                        wait=wait_strategy,
                        retry=_build_retry_condition(),
                        before_sleep=_tenacity_before_sleep,
                        reraise=True,
                    )
                    return await retryer(func, *args, **kwargs)

                return async_tenacity_wrapper
            else:
                @functools.wraps(func)
                def sync_tenacity_wrapper(*args, **kwargs) -> Any:
                    retryer = Retrying(
                        stop=stop_after_attempt(config.max_retries + 1),
                        wait=wait_strategy,
                        retry=_build_retry_condition(),
                        before_sleep=_tenacity_before_sleep,
                        reraise=True,
                    )
                    return retryer(func, *args, **kwargs)

                return sync_tenacity_wrapper

        # Fallback implementation if tenacity is ever unavailable
        if is_async:
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
                raise last_exception

            return async_wrapper
        else:
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

            return sync_wrapper

    return decorator


__all__ = [
    "RetryConfig",
    "retry_with_backoff",
    "_HAS_TENACITY",
]
