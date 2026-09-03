"""
💳 TruthGPT Cloud - Billing Subpackage
Exports subscription models, accounting manager, payment gateways, webhooks, and rate limiters.
"""

from .models import (
    UsageRecord,
    Invoice,
    ApiKeyInfo,
    WebhookSubscription,
    UserSubscription,
)

from .subscription import (
    SubscriptionManager,
    subscription_manager,
    TOKEN_PACK_CATALOG,
)

from .storage import AtomicJsonStorage
from .gateways import PaymentGatewayService
from .webhooks import (
    WebhookManager,
    WebhookEventPayload,
    webhook_manager,
)

from .rate_limiter import (
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    RateLimitExceeded,
    RateLimitExceededError,
    ConcurrencyLimitExceededError,
    cloud_rate_limiter,
    token_bucket_limiter,
    rate_limiter,
)

from ..core.exceptions import (
    QuotaExceededError,
    QuotaExceeded,
    TierUnauthorizedError,
    AuthenticationError,
)

__all__ = [
    # Domain Models
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "WebhookEventPayload",
    "UserSubscription",
    # Managers & Services
    "SubscriptionManager",
    "subscription_manager",
    "TOKEN_PACK_CATALOG",
    "PaymentGatewayService",
    "WebhookManager",
    "webhook_manager",
    "AtomicJsonStorage",
    # Rate Limiting
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "ConcurrencyLimitExceededError",
    "cloud_rate_limiter",
    "token_bucket_limiter",
    "rate_limiter",
    # Common Exceptions
    "QuotaExceededError",
    "QuotaExceeded",
    "TierUnauthorizedError",
    "AuthenticationError",
]
