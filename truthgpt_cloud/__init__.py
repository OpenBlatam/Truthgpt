"""
🌌 TruthGPT Cloud - Enterprise & Developer Multi-Tier Platform
The official cloud ecosystem for TruthGPT with Z3 SMT Formal Verification,
Merkle Proof Trees, Multi-Agent Swarm Orchestration, Tiered Subscriptions,
Semantic Proof Caching, Telemetry, and SOTA Research Paper Compilation.
"""

from .core import (
    CLOUD_PLATFORM_VERSION,
    CLOUD_API_VERSION,
    CloudTier,
    TierConfig,
    TIER_CONFIGURATIONS,
    get_tier_config,
    get_all_tiers,
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

from .security import (
    ApiKeyScope,
    ApiKeyMetadata,
    LedgerBlock,
    CloudSecurityManager,
    cloud_security,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    cloud_rate_limiter,
    token_bucket_limiter,
    rate_limiter,
)

from .billing import (
    UsageRecord,
    Invoice,
    ApiKeyInfo,
    WebhookSubscription,
    WebhookEventPayload,
    WebhookManager,
    webhook_manager,
    UserSubscription,
    SubscriptionManager,
    subscription_manager,
    AtomicJsonStorage,
    PaymentGatewayService,
)

from .verification import (
    ProofStep,
    ProofCertificate,
    ContractVerificationResult,
    MerkleTree,
    compute_merkle_root,
    verify_proof_certificate,
    verify_merkle_inclusion,
    CloudFormalVerifier,
    cloud_verifier,
)

from .swarm import (
    SwarmAgentNode,
    DebateRound,
    get_default_swarm_nodes,
    get_adversarial_team_nodes,
    SwarmExecutionTrace,
    CloudSwarmOrchestrator,
    cloud_swarm,
)

from .routing import (
    CloudInferenceResponse,
    StreamChunk,
    CloudIntelligenceRouter,
    cloud_router,
)

from .cache import (
    BaseProofCache,
    CachedProofEntry,
    CloudProofCache,
    proof_cache,
)

from .telemetry import (
    AuditLogEntry,
    CloudTelemetryCollector,
    cloud_telemetry,
    format_prometheus_metrics,
)

from .papers import (
    PaperItem,
    SOTA_PAPERS_CATALOG,
    get_all_papers,
    get_paper_by_id,
    CloudPaperCompiler,
    cloud_paper_compiler,
)

from .client import TruthGPTCloudClient

__version__ = CLOUD_PLATFORM_VERSION

__all__ = [
    # Version & Core
    "__version__",
    "CLOUD_PLATFORM_VERSION",
    "CLOUD_API_VERSION",
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
    # Security & RBAC
    "ApiKeyScope",
    "ApiKeyMetadata",
    "LedgerBlock",
    "CloudSecurityManager",
    "cloud_security",
    # Billing & Rate Limiting
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "WebhookEventPayload",
    "WebhookManager",
    "webhook_manager",
    "UserSubscription",
    "SubscriptionManager",
    "subscription_manager",
    "AtomicJsonStorage",
    "PaymentGatewayService",
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "cloud_rate_limiter",
    "token_bucket_limiter",
    "rate_limiter",
    # Formal Verification
    "ProofStep",
    "ProofCertificate",
    "ContractVerificationResult",
    "MerkleTree",
    "compute_merkle_root",
    "verify_proof_certificate",
    "verify_merkle_inclusion",
    "CloudFormalVerifier",
    "cloud_verifier",
    # Swarm Orchestration
    "SwarmAgentNode",
    "DebateRound",
    "get_default_swarm_nodes",
    "get_adversarial_team_nodes",
    "SwarmExecutionTrace",
    "CloudSwarmOrchestrator",
    "cloud_swarm",
    # Inference & Routing
    "CloudInferenceResponse",
    "StreamChunk",
    "CloudIntelligenceRouter",
    "cloud_router",
    # Cache & Telemetry
    "BaseProofCache",
    "CachedProofEntry",
    "CloudProofCache",
    "proof_cache",
    "AuditLogEntry",
    "CloudTelemetryCollector",
    "cloud_telemetry",
    "format_prometheus_metrics",
    # SOTA Papers
    "PaperItem",
    "SOTA_PAPERS_CATALOG",
    "get_all_papers",
    "get_paper_by_id",
    "CloudPaperCompiler",
    "cloud_paper_compiler",
    # Client SDK
    "TruthGPTCloudClient",
    # Domain Exceptions
    "TruthGPTCloudError",
    "AuthenticationError",
    "InvalidApiKeyError",
    "PermissionDeniedError",
    "TierUnauthorizedError",
    "QuotaExceededError",
    "QuotaExceeded",
    "FormalVerificationError",
    "VerificationError",
    "BatchVerificationError",
    "InvalidTierError",
    "ModelUnavailableError",
    "PaymentError",
    "PaymentRequiredError",
]

