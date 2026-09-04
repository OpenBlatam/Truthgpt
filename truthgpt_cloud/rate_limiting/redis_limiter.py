"""
⏱️ TruthGPT Cloud - Redis Distributed Rate Limiting & Quota Engine
Provides cluster-wide Sliding Window and Token Bucket rate limiting across multiple server nodes.
Backed by Redis sorted sets and atomic pipelines, with seamless in-memory fallback.
"""

import os
import time
import uuid
import logging
from typing import Optional, Any, Union

from ..core.tiers import CloudTier, get_tier_config
from ..core.exceptions import (
    RateLimitExceededError,
    QuotaExceededError,
)
from ..security.rate_limiter import (
    SlidingWindowRateLimiter as InMemorySlidingWindowLimiter,
    TokenBucketRateLimiter as InMemoryTokenBucketLimiter,
)

logger = logging.getLogger("TruthGPT.RedisRateLimiter")

_HAS_REDIS = False
try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False


class RedisSlidingWindowRateLimiter:
    """
    Cluster-wide sliding window rate limiter backed by Redis sorted sets (ZSET).
    Maintains precision request timestamps with millisecond accuracy across all TruthGPT Cloud worker pods.
    Falls back gracefully to local in-memory sliding window limiter if Redis is offline.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        client: Optional[Any] = None,
        key_prefix: str = "truthgpt:ratelimit:sw:",
        connection_timeout: float = 1.0,
    ):
        self.key_prefix = key_prefix
        self.connection_timeout = connection_timeout
        self.redis_url = redis_url or os.environ.get("TRUTHGPT_REDIS_URL", "redis://localhost:6379/0")

        self._in_memory_fallback = InMemorySlidingWindowLimiter()
        self._is_connected = False
        self._client: Optional[Any] = client

        if self._client is not None:
            self._is_connected = True
        elif _HAS_REDIS:
            self._connect()

    def _connect(self) -> None:
        """Attempt connection to Redis."""
        if not _HAS_REDIS:
            self._is_connected = False
            return
        try:
            pool = redis.ConnectionPool.from_url(
                self.redis_url,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout,
                max_connections=30,
            )
            client = redis.Redis(connection_pool=pool)
            client.ping()
            self._client = client
            self._is_connected = True
            logger.info(f"Connected to Redis distributed rate limiter at {self.redis_url}")
        except Exception as e:
            logger.debug(f"Redis rate limiter server unavailable ({e}); using in-memory fallback.")
            self._client = None
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        if not self._is_connected or self._client is None:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            self._is_connected = False
            return False

    def check_rate_limit(
        self,
        user_id: str,
        tier: Union[str, CloudTier],
        window_seconds: float = 60.0,
    ) -> bool:
        """
        Check and record request in cluster-wide sliding window.
        Raises RateLimitExceededError if requests exceed RPM limit in window.
        """
        config = get_tier_config(tier)
        max_requests = int(config.requests_per_minute)

        # Fallback to local memory if Redis unavailable
        if not self._is_connected or self._client is None:
            return self._in_memory_fallback.check_and_record(user_id, max_rpm=max_requests)

        key = f"{self.key_prefix}{user_id}"
        now = time.time()
        window_start = now - window_seconds
        member = f"{now:.6f}:{uuid.uuid4().hex[:8]}"

        try:
            pipe = self._client.pipeline(transaction=True)
            # 1. Evict entries older than sliding window
            pipe.zremrangebyscore(key, 0, window_start)
            # 2. Count requests remaining in active window
            pipe.zcard(key)
            # 3. Get oldest request in current window to calculate retry_after
            pipe.zrange(key, 0, 0, withscores=True)
            results = pipe.execute()

            current_count = results[1]
            oldest_entries = results[2]

            if current_count < max_requests:
                # Add current request and renew TTL
                pipe2 = self._client.pipeline(transaction=True)
                pipe2.zadd(key, {member: now})
                pipe2.expire(key, int(window_seconds * 2))
                pipe2.execute()
                return True
            else:
                # Calculate exact retry delay based on oldest request expiry
                if oldest_entries:
                    _, oldest_ts = oldest_entries[0]
                    retry_after = max(0.1, round((oldest_ts + window_seconds) - now, 2))
                else:
                    retry_after = round(window_seconds, 2)

                raise RateLimitExceededError(
                    message=f"Límite de velocidad en cluster ({max_requests} RPM) superado para {user_id}. Reintente en {retry_after}s.",
                    retry_after_seconds=retry_after,
                )
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.debug(f"Redis pipeline error in check_rate_limit: {e}; falling back to local limiter.")
            return self._in_memory_fallback.check_and_record(user_id, max_rpm=max_requests)

    def get_window_count(self, user_id: str, window_seconds: float = 60.0) -> int:
        """Get number of requests logged in current sliding window."""
        if not self._is_connected or self._client is None:
            reqs = self._in_memory_fallback._request_windows.get(user_id, [])
            now = time.time()
            return sum(1 for t in reqs if t >= now - window_seconds)
        key = f"{self.key_prefix}{user_id}"
        now = time.time()
        try:
            self._client.zremrangebyscore(key, 0, now - window_seconds)
            return int(self._client.zcard(key))
        except Exception:
            return 0

    def reset_user(self, user_id: str) -> None:
        """Reset rate limiter state for a specific user."""
        self._in_memory_fallback._request_windows.pop(user_id, None)
        self._in_memory_fallback._token_windows.pop(user_id, None)
        self._in_memory_fallback._concurrency_counts.pop(user_id, None)
        if self._is_connected and self._client is not None:
            try:
                self._client.delete(f"{self.key_prefix}{user_id}")
            except Exception:
                pass


class RedisTokenBucketRateLimiter:
    """
    Cluster-wide Token Bucket limiter backed by Redis with atomic consumption.
    Gracefully falls back to local in-memory token bucket limiter if Redis is offline.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        client: Optional[Any] = None,
        key_prefix: str = "truthgpt:ratelimit:tb:",
        connection_timeout: float = 1.0,
    ):
        self.key_prefix = key_prefix
        self.connection_timeout = connection_timeout
        self.redis_url = redis_url or os.environ.get("TRUTHGPT_REDIS_URL", "redis://localhost:6379/0")

        self._in_memory_fallback = InMemoryTokenBucketLimiter()
        self._is_connected = False
        self._client: Optional[Any] = client

        if self._client is not None:
            self._is_connected = True
        elif _HAS_REDIS:
            self._connect()

    def _connect(self) -> None:
        if not _HAS_REDIS:
            self._is_connected = False
            return
        try:
            pool = redis.ConnectionPool.from_url(
                self.redis_url,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout,
                max_connections=30,
            )
            client = redis.Redis(connection_pool=pool)
            client.ping()
            self._client = client
            self._is_connected = True
        except Exception:
            self._client = None
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        if not self._is_connected or self._client is None:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            self._is_connected = False
            return False

    def check_rate_limit(self, user_id: str, tier: Union[str, CloudTier], cost: float = 1.0) -> bool:
        """Check capacity and consume tokens. Raises QuotaExceededError if insufficient."""
        config = get_tier_config(tier)
        capacity = float(config.requests_per_minute)
        refill_rate = capacity / 60.0
        now = time.time()

        if not self._is_connected or self._client is None:
            return self._in_memory_fallback.check_rate_limit(user_id, tier, cost)

        key = f"{self.key_prefix}{user_id}"
        try:
            pipe = self._client.pipeline(transaction=True)
            pipe.hmget(key, ["tokens", "last_time"])
            results = pipe.execute()[0]

            raw_tokens, raw_time = results[0], results[1]
            if raw_tokens is not None and raw_time is not None:
                current_tokens = float(raw_tokens)
                last_time = float(raw_time)
                elapsed = max(0.0, now - last_time)
                current_tokens = min(capacity, current_tokens + elapsed * refill_rate)
            else:
                current_tokens = capacity

            if current_tokens >= cost:
                new_tokens = current_tokens - cost
                pipe2 = self._client.pipeline(transaction=True)
                pipe2.hset(key, mapping={"tokens": str(new_tokens), "last_time": str(now)})
                pipe2.expire(key, 120)
                pipe2.execute()
                return True
            else:
                retry_after = max(0.1, round((cost - current_tokens) / max(0.01, refill_rate), 2))
                raise QuotaExceededError(
                    message=f"Límite de velocidad en cluster (Token Bucket) excedido para {config.tier_id.value.upper()}. Reintente en {retry_after}s.",
                    limit=int(capacity),
                    consumed=int(capacity - current_tokens),
                )
        except QuotaExceededError:
            raise
        except Exception as e:
            logger.debug(f"Redis TokenBucket error: {e}; using fallback.")
            return self._in_memory_fallback.check_rate_limit(user_id, tier, cost)

    def reset_user(self, user_id: str) -> None:
        self._in_memory_fallback.reset_user(user_id)
        if self._is_connected and self._client is not None:
            try:
                self._client.delete(f"{self.key_prefix}{user_id}")
            except Exception:
                pass


__all__ = [
    "RedisSlidingWindowRateLimiter",
    "RedisTokenBucketRateLimiter",
    "_HAS_REDIS",
]
