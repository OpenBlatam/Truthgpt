"""
🏛️ TruthGPT Cloud - Core Subpackage
Defines subscription tier models, exceptions, constants, foundational types,
abstract lifecycle interfaces, component registry, configuration, and factory.
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

from .context import (
    TruthGPTCloudContext,
    get_cloud_context,
    create_isolated_context,
    set_cloud_context,
    reset_cloud_context,
)

from .interfaces import (
    IStorageBackend,
    IProofCache,
    IFormalVerifier,
    ISwarmOrchestrator,
    IIntelligenceRouter,
    IRateLimiter,
    ISubscriptionManager,
    IPaymentGateway,
    ITelemetryCollector,
    ICircuitBreaker,
    IWebhookManager,
    IPaperCompiler,
)

from .registry import CloudRegistry

from .config import (
    CloudConfigValidationError,
    CloudStorageConfig,
    CloudCacheConfig,
    CloudVerifierConfig,
    CloudRoutingConfig,
    CloudRateLimiterConfig,
    CloudTelemetryConfig,
    CloudResilienceConfig,
    CloudPlatformConfig,
)

from .factory import CloudFactory

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
    # Interfaces
    "IStorageBackend",
    "IProofCache",
    "IFormalVerifier",
    "ISwarmOrchestrator",
    "IIntelligenceRouter",
    "IRateLimiter",
    "ISubscriptionManager",
    "IPaymentGateway",
    "ITelemetryCollector",
    "ICircuitBreaker",
    "IWebhookManager",
    "IPaperCompiler",
    # Registry & Architecture
    "CloudRegistry",
    # Configuration
    "CloudConfigValidationError",
    "CloudStorageConfig",
    "CloudCacheConfig",
    "CloudVerifierConfig",
    "CloudRoutingConfig",
    "CloudRateLimiterConfig",
    "CloudTelemetryConfig",
    "CloudResilienceConfig",
    "CloudPlatformConfig",
    # Factory
    "CloudFactory",
    # Context & Dependency Injection
    "TruthGPTCloudContext",
    "get_cloud_context",
    "create_isolated_context",
    "set_cloud_context",
    "reset_cloud_context",
]
