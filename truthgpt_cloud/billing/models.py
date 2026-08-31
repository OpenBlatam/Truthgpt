"""
💳 TruthGPT Cloud - Billing & Subscription Domain Models
"""

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from ..core.tiers import CloudTier


@dataclass
class UsageRecord:
    total_tokens_consumed: int = 0
    tokens_consumed_today: int = 0
    verifications_run: int = 0
    swarm_sessions_count: int = 0
    last_reset_timestamp: float = field(default_factory=time.time)
    daily_request_count: int = 0


@dataclass
class Invoice:
    invoice_id: str
    user_id: str
    tier_id: str
    amount_usd: float
    billing_cycle: str  # "monthly" or "yearly"
    payment_method: str  # "stripe_card", "crypto_usdc", "crypto_eth", "wire_transfer"
    status: str  # "paid", "pending", "refunded"
    created_at: str


@dataclass
class ApiKeyInfo:
    key_id: str
    key_prefix: str
    name: str = "Default API Key"
    created_at: float = field(default_factory=time.time)
    last_used_at: Optional[float] = None
    is_active: bool = True
    scopes: List[str] = field(default_factory=lambda: ["all"])


@dataclass
class WebhookSubscription:
    webhook_id: str
    user_id: str
    endpoint_url: str
    events: List[str] = field(default_factory=lambda: ["invoice.paid", "quota.warning"])
    is_active: bool = True
    secret_key: str = ""


@dataclass
class UserSubscription:
    user_id: str
    email: str
    name: str
    tier: CloudTier = CloudTier.FREE
    billing_cycle: str = "monthly"
    status: str = "active"  # "active", "trialing", "past_due", "canceled"
    api_keys: List[str] = field(default_factory=list)
    subscription_start_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    next_billing_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    usage: UsageRecord = field(default_factory=UsageRecord)
    invoices: List[Invoice] = field(default_factory=list)
    api_key_details: List[ApiKeyInfo] = field(default_factory=list)
    webhooks: List[WebhookSubscription] = field(default_factory=list)
    custom_limits: Optional[Dict[str, Any]] = None


__all__ = [
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "UserSubscription",
]
