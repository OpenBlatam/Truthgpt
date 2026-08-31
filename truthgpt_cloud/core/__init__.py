"""
Core package for TruthGPT Cloud.
Exposes domain tiers, configurations, and domain exception classes.
"""

from .exceptions import (
    TruthGPTCloudError,
    AuthenticationError,
    InvalidApiKeyError,
    PermissionDeniedError,
    TierUnauthorizedError,
    QuotaExceededError,
    QuotaExceeded,
    RateLimitExceededError,
    RateLimitExceeded,
    ConcurrencyLimitExceededError,
    FormalVerificationError,
    VerificationError,
    BatchVerificationError,
    InvalidTierError,
    ModelUnavailableError,
    PaymentError,
    PaymentRequiredError,
)

from .tiers import (
    CloudTier,
    TierConfig,
    TIER_CONFIGURATIONS,
    get_tier_config,
    get_all_tiers
)

__all__ = [
    "TruthGPTCloudError",
    "AuthenticationError",
    "InvalidApiKeyError",
    "PermissionDeniedError",
    "TierUnauthorizedError",
    "QuotaExceededError",
    "QuotaExceeded",
    "RateLimitExceededError",
    "RateLimitExceeded",
    "ConcurrencyLimitExceededError",
    "FormalVerificationError",
    "VerificationError",
    "BatchVerificationError",
    "InvalidTierError",
    "ModelUnavailableError",
    "PaymentError",
    "PaymentRequiredError",
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
]
