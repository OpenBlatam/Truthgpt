"""
🚨 TruthGPT Cloud - Custom Exception Hierarchy (Re-export)
Provides structured domain exceptions for billing, quotas, formal verification, and API routing.
"""

from .core.exceptions import (
    TruthGPTCloudError,
    QuotaExceededError,
    QuotaExceeded,
    TierUnauthorizedError,
    AuthenticationError,
    PermissionDeniedError,
    VerificationError,
    FormalVerificationError,
    BatchVerificationError,
    RateLimitExceededError,
    RateLimitExceeded,
    ConcurrencyLimitExceededError,
    InvalidApiKeyError,
    InvalidTierError,
    ModelUnavailableError,
    PaymentRequiredError,
    PaymentError,
)

__all__ = [
    "TruthGPTCloudError",
    "QuotaExceededError",
    "QuotaExceeded",
    "TierUnauthorizedError",
    "AuthenticationError",
    "PermissionDeniedError",
    "VerificationError",
    "FormalVerificationError",
    "BatchVerificationError",
    "RateLimitExceededError",
    "RateLimitExceeded",
    "ConcurrencyLimitExceededError",
    "InvalidApiKeyError",
    "InvalidTierError",
    "ModelUnavailableError",
    "PaymentRequiredError",
    "PaymentError",
]
