"""
🏛️ TruthGPT Cloud - Core Subpackage
Defines subscription tier models, exceptions, constants, and foundational types.
"""

from .constants import (
    CLOUD_PLATFORM_VERSION,
    CLOUD_API_VERSION,
    DEFAULT_SLIDING_WINDOW_SECONDS,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_TELEMETRY_MAX_HISTORY,
    DEFAULT_SMT_TIMEOUT_MS,
    DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS,
    DEFAULT_CERTIFICATE_SECRET,
    DEFAULT_WEBHOOK_SECRET,
    STANDARD_WARMUP_THEOREMS,
)

from .tiers import (
    CloudTier,
    TierConfig,
    TIER_CONFIGURATIONS,
    get_tier_config,
    get_all_tiers,
)

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

from .types import (
    CloudFeature,
    VerificationEngineType,
    ProofStatus,
    SwarmTopologyType,
    PaymentMethodType,
    AlertComparisonOp,
    CloudModuleInfo,
    CloudPlatformStatus,
)

from .schemas import (
    ProofCertificateSchema,
    InferenceRequestSchema,
    InferenceResponseSchema,
    TierConfigSchema,
    AuditLogSchema,
    AlertRuleSchema,
    UsageRecordSchema,
    InvoiceSchema,
    ApiKeyInfoSchema,
    WebhookSubscriptionSchema,
    UserSubscriptionSchema,
    validate_subscription_db,
)

__all__ = [
    # Constants
    "CLOUD_PLATFORM_VERSION",
    "CLOUD_API_VERSION",
    "DEFAULT_SLIDING_WINDOW_SECONDS",
    "DEFAULT_CACHE_MAX_ENTRIES",
    "DEFAULT_TELEMETRY_MAX_HISTORY",
    "DEFAULT_SMT_TIMEOUT_MS",
    "DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS",
    "DEFAULT_CERTIFICATE_SECRET",
    "DEFAULT_WEBHOOK_SECRET",
    "STANDARD_WARMUP_THEOREMS",
    # Tiers
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
    # Exceptions
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
    # Foundational Types & Enums
    "CloudFeature",
    "VerificationEngineType",
    "ProofStatus",
    "SwarmTopologyType",
    "PaymentMethodType",
    "AlertComparisonOp",
    "CloudModuleInfo",
    "CloudPlatformStatus",
    # Pydantic Schemas
    "ProofCertificateSchema",
    "InferenceRequestSchema",
    "InferenceResponseSchema",
    "TierConfigSchema",
    "AuditLogSchema",
    "AlertRuleSchema",
    "UsageRecordSchema",
    "InvoiceSchema",
    "ApiKeyInfoSchema",
    "WebhookSubscriptionSchema",
    "UserSubscriptionSchema",
    "validate_subscription_db",
]
