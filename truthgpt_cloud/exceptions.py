"""
🚨 TruthGPT Cloud - Custom Exception Hierarchy (Re-export)
Provides structured domain exceptions for billing, quotas, formal verification, and API routing.
"""

from .core.exceptions import (
    TruthGPTCloudError,
    QuotaExceededError,
    TierUnauthorizedError,
    AuthenticationError,
    PermissionDeniedError,
    VerificationError,
    FormalVerificationError,
    BatchVerificationError,
    RateLimitExceededError,
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
    "TierUnauthorizedError",
    "AuthenticationError",
    "PermissionDeniedError",
    "VerificationError",
    "FormalVerificationError",
    "BatchVerificationError",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "InvalidApiKeyError",
    "InvalidTierError",
    "ModelUnavailableError",
    "PaymentRequiredError",
    "PaymentError",
]
