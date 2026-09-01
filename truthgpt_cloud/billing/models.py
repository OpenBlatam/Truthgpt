"""
💳 TruthGPT Cloud - Billing & Subscription Domain Models
"""

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from ..core.tiers import CloudTier


@dataclass
class UsageRecord:
    total_tokens_consumed: int = 0
    tokens_consumed_today: int = 0
    verifications_run: int = 0
    swarm_sessions_count: int = 0
    last_reset_timestamp: float = field(default_factory=time.time)
    daily_request_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Invoice:
    invoice_id: str
    user_id: str
    tier_id: str
    amount_usd: float
    billing_cycle: str = "monthly"  # "monthly" or "yearly"
    payment_method: str = "stripe_card"  # "stripe_card", "crypto_usdc", "crypto_eth", "wire_transfer"
    status: str = "paid"  # "paid", "pending", "refunded"
    discount_applied_usd: float = 0.0
    promo_code: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_text_receipt(self) -> str:
        """Render a clean text invoice receipt."""
        return (
            f"========================================================\n"
            f" 🧾 TRUTHGPT CLOUD - OFFICIAL INVOICE RECEIPT\n"
            f"========================================================\n"
            f"Invoice ID:      {self.invoice_id}\n"
            f"Customer ID:     {self.user_id}\n"
            f"Subscription:    {self.tier_id.upper()} ({self.billing_cycle})\n"
            f"Payment Method:  {self.payment_method}\n"
            f"Status:          {self.status.upper()}\n"
            f"Date Issued:     {self.created_at}\n"
            f"--------------------------------------------------------\n"
            f"Subtotal:        ${self.amount_usd + self.discount_applied_usd:.2f} USD\n"
            f"Discount:       -${self.discount_applied_usd:.2f} USD {f'({self.promo_code})' if self.promo_code else ''}\n"
            f"Total Paid:      ${self.amount_usd:.2f} USD\n"
            f"========================================================\n"
        )



@dataclass
class ApiKeyInfo:
    key: str = ""
    key_id: str = ""
    key_prefix: str = ""
    label: str = "Default API Key"
    name: str = "Default API Key"
    created_at: float = field(default_factory=time.time)
    last_used_at: Optional[float] = None
    is_active: bool = True
    scopes: List[str] = field(default_factory=lambda: ["all"])

    def __post_init__(self):
        if not self.key_prefix and self.key:
            self.key_prefix = self.key[:16] + "..."
        if not self.label and self.name:
            self.label = self.name
        elif not self.name and self.label:
            self.name = self.label

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WebhookSubscription:
    webhook_id: str
    user_id: str
    endpoint_url: str = ""
    target_url: str = ""
    events: List[str] = field(default_factory=lambda: ["invoice.paid", "quota.warning"])
    subscribed_events: List[str] = field(default_factory=lambda: ["invoice.paid", "quota.warning"])
    is_active: bool = True
    secret_key: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.target_url and self.endpoint_url:
            self.target_url = self.endpoint_url
        elif not self.endpoint_url and self.target_url:
            self.endpoint_url = self.target_url
        if not self.subscribed_events and self.events:
            self.subscribed_events = self.events
        elif not self.events and self.subscribed_events:
            self.events = self.subscribed_events

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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

    @property
    def api_keys_detail(self) -> List[ApiKeyInfo]:
        """Backward compatibility alias for api_key_details."""
        return self.api_key_details

    @api_keys_detail.setter
    def api_keys_detail(self, value: List[ApiKeyInfo]) -> None:
        self.api_key_details = value

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value if isinstance(self.tier, CloudTier) else str(self.tier)
        return d


__all__ = [
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "UserSubscription",
]
