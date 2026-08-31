"""
🚨 TruthGPT Cloud - Domain Exception Hierarchy
Provides typed domain errors for billing, quotas, formal verification, authentication, and routing.
"""

from typing import Optional


class TruthGPTCloudError(Exception):
    """Base exception for all TruthGPT Cloud operations."""
    def __init__(self, message: str = "An error occurred in TruthGPT Cloud.", code: str = "CLOUD_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class AuthenticationError(TruthGPTCloudError):
    """Raised when API key or user authentication fails."""
    def __init__(self, message: str = "Invalid or missing TruthGPT Cloud API key."):
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401)


class InvalidApiKeyError(AuthenticationError):
    """Raised when an API key is malformed, expired, or revoked."""
    def __init__(self, message: str = "Clave de API inválida, expirada o revocada."):
        super().__init__(message)
        self.code = "INVALID_API_KEY"


class PermissionDeniedError(TruthGPTCloudError):
    """Raised when user attempts an action not permitted by their tier or scopes."""
    def __init__(self, message: str = "Permission denied for this operation on the active tier."):
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)


class TierUnauthorizedError(ValueError, PermissionDeniedError):
    """Raised when a requested feature or model requires a higher subscription tier."""
    def __init__(
        self,
        required_tier: str = "pro",
        current_tier: str = "free",
        feature: str = "advanced_feature",
        message: Optional[str] = None
    ):
        msg = message or f"La característica '{feature}' requiere el plan {required_tier.upper()} (Plan actual: {current_tier.upper()})."
        super().__init__(msg)
        self.code = "TIER_UNAUTHORIZED"
        self.required_tier = required_tier
        self.current_tier = current_tier
        self.feature = feature


class QuotaExceededError(PermissionError, TruthGPTCloudError):
    """Raised when user daily token limit or compute quota is reached."""
    def __init__(
        self,
        message: str = "Daily token quota exceeded. Upgrade tier to continue.",
        limit: int = 0,
        consumed: int = 0
    ):
        super().__init__(message)
        self.message = message
        self.code = "QUOTA_EXCEEDED"
        self.status_code = 402
        self.limit = limit
        self.consumed = consumed


# Alias for backward compatibility
QuotaExceeded = QuotaExceededError


class RateLimitExceededError(TruthGPTCloudError):
    """Raised when requests per minute (RPM) or concurrency limit is violated."""
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please throttle your requests.",
        retry_after_seconds: float = 5.0
    ):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)
        self.retry_after_seconds = retry_after_seconds


# Alias for backward compatibility
RateLimitExceeded = RateLimitExceededError


class ConcurrencyLimitExceededError(RateLimitExceededError):
    """Raised when concurrent request limit is reached for user's tier."""
    def __init__(self, message: str = "Concurrent request limit exceeded.", max_concurrent: int = 1):
        super().__init__(message)
        self.code = "CONCURRENCY_LIMIT_EXCEEDED"
        self.max_concurrent = max_concurrent


class FormalVerificationError(TruthGPTCloudError):
    """Raised when SMT theorem proving encounters solver failure or contradiction."""
    def __init__(self, message: str = "Formal verification constraint solver encountered an error.", solver: str = "Z3 SMT"):
        super().__init__(message, code="FORMAL_VERIFICATION_ERROR", status_code=422)
        self.solver = solver


# Alias for backward compatibility
VerificationError = FormalVerificationError


class BatchVerificationError(FormalVerificationError):
    """Raised when one or more claims in a batch verification fail."""
    def __init__(self, message: str = "Batch verification failed.", failed_count: int = 0, total_count: int = 0):
        super().__init__(message)
        self.code = "BATCH_VERIFICATION_ERROR"
        self.failed_count = failed_count
        self.total_count = total_count


class InvalidTierError(TruthGPTCloudError):
    """Raised when an invalid subscription tier is requested."""
    def __init__(self, message: str = "Invalid tier specified."):
        super().__init__(message, code="INVALID_TIER", status_code=400)


class ModelUnavailableError(TruthGPTCloudError):
    """Raised when a requested frontier model is not available for the active tier."""
    def __init__(self, message: str = "Requested model is not available in current subscription tier."):
        super().__init__(message, code="MODEL_UNAVAILABLE", status_code=403)


class PaymentError(TruthGPTCloudError):
    """Raised when payment gateway or invoice processing fails."""
    def __init__(self, message: str = "Payment processing failed."):
        super().__init__(message, code="PAYMENT_ERROR", status_code=402)


class PaymentRequiredError(PaymentError):
    """Raised when an unpaid invoice or past due balance blocks execution."""
    def __init__(self, message: str = "Pago requerido para continuar con la ejecución."):
        super().__init__(message)
        self.code = "PAYMENT_REQUIRED"


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
]
