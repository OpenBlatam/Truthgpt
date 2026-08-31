"""
🔒 TruthGPT Cloud - Security, RBAC & Token Bucket Rate Limiting
Provides enterprise-grade rate limiting, API key hashing & scopes, and request authorization.
"""

import time
import hashlib
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple

from .core.tiers import CloudTier, get_tier_config
from .core.exceptions import QuotaExceededError, AuthenticationError, TierUnauthorizedError

logger = logging.getLogger("TruthGPT.CloudSecurity")


class ApiKeyScope(str, Enum):
    ALL = "all"
    INFERENCE = "inference"
    VERIFY = "verify"
    SWARM = "swarm"
    ADMIN = "admin"
    BILLING = "billing"


@dataclass
class ApiKeyMetadata:
    key_id: str
    key_hash: str
    key_prefix: str
    user_id: str
    name: str = "Default Key"
    scopes: Set[ApiKeyScope] = field(default_factory=lambda: {ApiKeyScope.ALL})
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True
    last_used_at: Optional[float] = None


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter supporting requests-per-minute (RPM) and concurrent burst limits.
    """

    def __init__(self):
        # user_id -> (current_tokens, last_updated_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = {}

    def check_rate_limit(self, user_id: str, tier: CloudTier, cost: float = 1.0) -> bool:
        """
        Verify if request is permitted under user's tier RPM capacity.
        Raises QuotaExceededError if rate limit is exceeded.
        """
        config = get_tier_config(tier)
        capacity = float(config.requests_per_minute)
        refill_rate = capacity / 60.0  # tokens per second
        now = time.time()

        if user_id not in self._buckets:
            self._buckets[user_id] = (capacity, now)

        current_tokens, last_time = self._buckets[user_id]
        
        # Refill tokens based on elapsed time
        elapsed = max(0.0, now - last_time)
        current_tokens = min(capacity, current_tokens + elapsed * refill_rate)

        if current_tokens >= cost:
            self._buckets[user_id] = (current_tokens - cost, now)
            return True
        else:
            retry_after = round((cost - current_tokens) / refill_rate, 2)
            raise QuotaExceededError(
                message=f"Límite de velocidad (RPM) excedido para el plan {tier.value.upper()}. Reintente en {retry_after}s.",
                limit=int(capacity),
                consumed=int(capacity - current_tokens)
            )

    def reset_user(self, user_id: str) -> None:
        """Reset rate limiter bucket for a user."""
        if user_id in self._buckets:
            del self._buckets[user_id]


class CloudSecurityManager:
    """
    Manages API keys, role-based access control (RBAC), and cryptographic key verification.
    """

    def __init__(self):
        self.rate_limiter = TokenBucketRateLimiter()
        self._key_registry: Dict[str, ApiKeyMetadata] = {}  # key_hash -> ApiKeyMetadata

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Compute SHA-256 digest of raw API key."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def generate_api_key(
        self,
        user_id: str,
        name: str = "Production API Key",
        scopes: Optional[Set[ApiKeyScope]] = None
    ) -> Tuple[str, ApiKeyMetadata]:
        """
        Create a new API key for a user and register its cryptographic hash.
        """
        raw_key = f"tgpt_cloud_live_{uuid.uuid4().hex}"
        key_hash = self.hash_key(raw_key)
        prefix = raw_key[:16] + "..."
        
        meta = ApiKeyMetadata(
            key_id=f"key_{uuid.uuid4().hex[:10]}",
            key_hash=key_hash,
            key_prefix=prefix,
            user_id=user_id,
            name=name,
            scopes=scopes or {ApiKeyScope.ALL}
        )
        self._key_registry[key_hash] = meta
        return raw_key, meta

    def validate_api_key(
        self,
        raw_key: str,
        required_scope: Optional[ApiKeyScope] = None
    ) -> ApiKeyMetadata:
        """
        Validate raw key against registry and verify authorization scopes.
        """
        key_hash = self.hash_key(raw_key)
        meta = self._key_registry.get(key_hash)
        
        if not meta or not meta.is_active:
            raise AuthenticationError("Clave de API no válida o revocada.")
            
        if meta.expires_at and time.time() > meta.expires_at:
            meta.is_active = False
            raise AuthenticationError("La clave de API ha expirado.")

        if required_scope and (ApiKeyScope.ALL not in meta.scopes and required_scope not in meta.scopes):
            raise TierUnauthorizedError(
                required_tier="API Scope",
                current_tier="Restricted",
                feature=f"Scope requerido: {required_scope.value}"
            )

        meta.last_used_at = time.time()
        return meta

    def revoke_key(self, key_hash: str) -> bool:
        """Revoke an active key."""
        if key_hash in self._key_registry:
            self._key_registry[key_hash].is_active = False
            return True
        return False


# Global Security Instance
cloud_security = CloudSecurityManager()

__all__ = [
    "ApiKeyScope",
    "ApiKeyMetadata",
    "TokenBucketRateLimiter",
    "CloudSecurityManager",
    "cloud_security",
]
