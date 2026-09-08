"""
⏱️ TruthGPT Cloud - Rate Limiting & Concurrency Package
Provides in-memory Sliding Window & Token Bucket rate limiters,
distributed Redis backends, and concurrency enforcement.
"""

from typing import Optional, Literal, Union

from .sliding_window import (
    SlidingWindowRateLimiter,
    RateLimitExceeded,
    RateLimitExceededError,
    ConcurrencyLimitExceededError,
    cloud_rate_limiter,
    rate_limiter,
)
from .token_bucket import (
    TokenBucketRateLimiter,
    token_bucket_limiter,
)
from .redis_limiter import (
    RedisSlidingWindowRateLimiter,
    RedisTokenBucketRateLimiter,
    _HAS_REDIS,
)


def get_rate_limiter(
    kind: Literal["sliding_window", "token_bucket"] = "sliding_window",
    backend: Literal["memory", "redis"] = "memory",
    redis_client: Optional[object] = None,
    prefix: str = "truthgpt:cloud:ratelimit",
) -> Union[
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    RedisSlidingWindowRateLimiter,
    RedisTokenBucketRateLimiter,
]:
    """
    Factory function to obtain a configured rate limiter instance.

    Args:
        kind: 'sliding_window' for timestamp logs, or 'token_bucket' for leaky bucket.
        backend: 'memory' for in-process thread-safe limiter, 'redis' for cluster-wide distributed limiter.
        redis_client: Optional Redis connection instance for redis backend.
        prefix: Redis key namespace.
    """
    if backend == "redis":
        if kind == "token_bucket":
            return RedisTokenBucketRateLimiter(redis_client=redis_client, key_prefix=prefix)
        return RedisSlidingWindowRateLimiter(redis_client=redis_client, key_prefix=prefix)
    else:
        if kind == "token_bucket":
            return TokenBucketRateLimiter()
        return SlidingWindowRateLimiter()


__all__ = [
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
    "RedisSlidingWindowRateLimiter",
    "RedisTokenBucketRateLimiter",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "cloud_rate_limiter",
    "token_bucket_limiter",
    "rate_limiter",
    "get_rate_limiter",
    "_HAS_REDIS",
]
