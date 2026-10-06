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
    mask_api_key,
    hash_api_key,
)

from .storage import AtomicJsonStorage
from .gateways import PaymentGatewayService
from .webhooks import (
    WebhookManager,
    WebhookEventPayload,
    WebhookDeliveryAttempt,
    DeadLetterEntry,
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

from .token_packs import (
    TOKEN_PACK_CATALOG,
    get_token_pack_catalog,
    get_token_pack,
    validate_token_pack_id,
)
from .promo import (
    VALID_PROMO_CODES,
    calculate_promo_discount,
)
from .churn_lifecycle import (
    calculate_user_activity_metrics,
    compute_churn_and_usage_dashboard,
)
from .invoicing import (
    charge_user_handler,
    charge_usage_tokens_handler,
    get_user_invoices_handler,
    get_invoice_receipt_handler,
)

__all__ = [
    # Domain Models
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "WebhookEventPayload",
    "WebhookDeliveryAttempt",
    "DeadLetterEntry",
    "UserSubscription",
    # Managers & Services
    "SubscriptionManager",
    "subscription_manager",
    "TOKEN_PACK_CATALOG",
    "get_token_pack_catalog",
    "get_token_pack",
    "validate_token_pack_id",
    "VALID_PROMO_CODES",
    "calculate_promo_discount",
    "calculate_user_activity_metrics",
    "compute_churn_and_usage_dashboard",
    "charge_user_handler",
    "charge_usage_tokens_handler",
    "get_user_invoices_handler",
    "get_invoice_receipt_handler",
    "mask_api_key",
    "hash_api_key",
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
