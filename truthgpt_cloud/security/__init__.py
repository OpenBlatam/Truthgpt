"""
🔒 TruthGPT Cloud - Security & Access Subpackage
Exports rate limiting, API key management, and cryptographic access control.
"""

from .models import ApiKeyScope, ApiKeyMetadata, LedgerBlock
from .manager import (
    CloudSecurityManager,
    cloud_security,
    _HAS_CRYPTOGRAPHY,
    create_session_jwt,
    verify_session_jwt,
    decode_jwt_unverified,
    _HAS_PYJWT,
)
from .rate_limiter import (
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    RateLimitExceeded,
    RateLimitExceededError,
    ConcurrencyLimitExceededError,
    rate_limiter,
    cloud_rate_limiter,
    token_bucket_limiter,
)
from ..core.exceptions import AuthenticationError

__all__ = [
    "ApiKeyScope",
    "ApiKeyMetadata",
    "LedgerBlock",
    "CloudSecurityManager",
    "cloud_security",
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "cloud_rate_limiter",
    "token_bucket_limiter",
    "rate_limiter",
    "_HAS_CRYPTOGRAPHY",
    "create_session_jwt",
    "verify_session_jwt",
    "decode_jwt_unverified",
    "_HAS_PYJWT",
    "AuthenticationError",
]

