"""
🌌 TruthGPT Cloud - Enterprise & Developer Multi-Tier Platform
The official cloud ecosystem for TruthGPT with Z3 SMT Formal Verification,
Merkle Proof Trees, Multi-Agent Swarm Orchestration, and Tiered Subscription Management.
"""

from .core.tiers import (
    CloudTier,
    TierConfig,
    TIER_CONFIGURATIONS,
    get_tier_config,
    get_all_tiers
)

from .billing import (
    UserSubscription,
    Invoice,
    UsageRecord,
    SubscriptionManager,
    subscription_manager,
    PaymentGatewayService,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    RateLimitExceeded,
    rate_limiter,
    WebhookManager,
    WebhookSubscription,
    WebhookEventPayload,
    webhook_manager
)

from .verification import (
    ProofCertificate,
    ContractVerificationResult,
    MerkleTree,
    CloudFormalVerifier,
    cloud_verifier
)

from .swarm_cloud import (
    SwarmAgentNode,
    SwarmExecutionTrace,
    CloudSwarmOrchestrator,
    cloud_swarm
)

from .engine_router import (
    CloudInferenceResponse,
    CloudIntelligenceRouter,
    cloud_router
)

from .client import TruthGPTCloudClient

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
    PaymentError
)

__version__ = "2.0.0-cloud"
__all__ = [
    # Tiers
    "CloudTier",
    "TierConfig",
    "TIER_CONFIGURATIONS",
    "get_tier_config",
    "get_all_tiers",
    
    # Billing & Rate Limiting
    "UserSubscription",
    "Invoice",
    "UsageRecord",
    "SubscriptionManager",
    "subscription_manager",
    "PaymentGatewayService",
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "rate_limiter",
    "WebhookManager",
    "WebhookSubscription",
    "WebhookEventPayload",
    "webhook_manager",
    
    # Formal Verification
    "ProofCertificate",
    "ContractVerificationResult",
    "MerkleTree",
    "CloudFormalVerifier",
    "cloud_verifier",
    
    # Swarm Orchestration
    "SwarmAgentNode",
    "SwarmExecutionTrace",
    "CloudSwarmOrchestrator",
    "cloud_swarm",
    
    # Inference & Routing
    "CloudInferenceResponse",
    "CloudIntelligenceRouter",
    "cloud_router",
    
    # Client SDK
    "TruthGPTCloudClient",
    
    # Exceptions
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
    
    "__version__",
]
