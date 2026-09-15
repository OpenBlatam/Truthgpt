"""
💳 TruthGPT Cloud - Client Billing & Subscription Operations
Encapsulates tier management, API key rotation, metered usage accounting,
token pack purchases, and invoice queries for TruthGPTCloudClient.
"""

from typing import Dict, List, Optional, Any, Union
from ..core.tiers import CloudTier, TierConfig, get_tier_config, get_all_tiers
from ..billing.subscription import UserSubscription


class ClientBillingMixin:
    """Mixin providing billing, subscription, and key management operations for TruthGPTCloudClient."""

    sub_manager: Any
    user: Optional[UserSubscription] = None
    user_id: str = ""
    api_key: str = ""

    # ---------------------------------------------------------------------------
    # Properties & Entitlements
    # ---------------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        """Returns True if the client possesses an active user account and valid API key."""
        return bool(self.user_id and self.api_key and self.user and self.user.status == "active")

    @property
    def tier(self) -> CloudTier:
        """Return the active CloudTier of the client."""
        user = self.sub_manager.get_user(self.user_id)
        return user.tier if user else CloudTier.FREE

    @property
    def tier_config(self) -> TierConfig:
        """Return the TierConfig defining RPM, token limits, and verification depths for active tier."""
        return get_tier_config(self.tier)

    # ---------------------------------------------------------------------------
    # User Profile & Quota Summaries
    # ---------------------------------------------------------------------------

    def get_user_info(self) -> Dict[str, Any]:
        """Return structured summary of active user account, subscription tier, and quotas."""
        return self.sub_manager.get_user_status_summary(self.user_id)

    whoami = get_user_info
    profile = get_user_info

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get live token quota, tier status, and billing metrics."""
        return self.sub_manager.get_user_status_summary(self.user_id)

    def get_subscription_profile(self) -> Dict[str, Any]:
        """Get current user subscription profile, tier limits and active status."""
        user = self.sub_manager.get_user(self.user_id)
        if user:
            return user.to_dict()
        return {"user_id": self.user_id, "tier": self.tier.value, "status": "active"}

    def get_usage_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed usage analytics and token economics breakdown."""
        uid = user_id or self.user_id
        return self.sub_manager.get_usage_analytics(uid)

    # ---------------------------------------------------------------------------
    # Tier Changes & Purchases
    # ---------------------------------------------------------------------------

    def upgrade_tier(
        self,
        target_tier: Union[str, CloudTier],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """Upgrade subscription tier with checkout simulation."""
        tier_enum = CloudTier(target_tier.lower()) if isinstance(target_tier, str) else target_tier
        return self.sub_manager.upgrade_subscription(
            user_id=self.user_id,
            target_tier=tier_enum,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )

    @staticmethod
    def list_available_tiers() -> List[Dict[str, Any]]:
        """List all subscription tier offerings and pricing matrices."""
        return get_all_tiers()

    def get_token_pack_catalog(self) -> List[Dict[str, Any]]:
        """Return available on-demand top-up token packs and prices."""
        return self.sub_manager.get_token_pack_catalog()

    def purchase_token_pack(
        self,
        pack_id: str,
        payment_method: str = "stripe_card",
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase on-demand top-up tokens, processing immediate payment and adding tokens to user balance.
        """
        return self.sub_manager.purchase_token_pack(
            user_id=self.user_id,
            pack_id=pack_id,
            payment_method=payment_method,
            promo_code=promo_code
        )

    def charge_service(
        self,
        amount_usd: float,
        description: str = "TruthGPT Cloud Service Compute",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """
        Directly charge the TruthGPT user for cloud service operations, emitting an official invoice receipt.
        """
        return self.sub_manager.charge_user(
            user_id=self.user_id,
            amount_usd=amount_usd,
            description=description,
            payment_method=payment_method
        )

    def charge_usage_tokens(
        self,
        tokens_consumed: int,
        unit_price_per_1k_tokens: float = 0.002,
        description: Optional[str] = None,
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """
        Charge user for metered token consumption.
        """
        return self.sub_manager.charge_usage_tokens(
            user_id=self.user_id,
            tokens_consumed=tokens_consumed,
            unit_price_per_1k_tokens=unit_price_per_1k_tokens,
            description=description,
            payment_method=payment_method
        )

    def get_invoices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve billing invoices and receipts for the current TruthGPT user."""
        return self.sub_manager.get_user_invoices(self.user_id, limit=limit)

    # ---------------------------------------------------------------------------
    # API Key Lifecycle
    # ---------------------------------------------------------------------------

    def generate_api_key(self, label: str = "Default Key", scopes: Optional[List[str]] = None) -> str:
        """Generate a new dedicated API key."""
        return self.sub_manager.generate_new_api_key(self.user_id, label=label, scopes=scopes)

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an active API key."""
        return self.sub_manager.revoke_api_key(self.user_id, api_key)

    def rotate_api_key(
        self,
        old_api_key: str,
        user_id: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically rotate an existing API key for current user."""
        target_uid = user_id or (self.user.user_id if self.user else "usr_client_default")
        new_key, key_detail = self.sub_manager.rotate_api_key(
            user_id=target_uid,
            old_api_key=old_api_key,
            label=label,
        )
        return {
            "success": True,
            "user_id": target_uid,
            "new_api_key": new_key,
            "key_details": key_detail.to_dict() if hasattr(key_detail, "to_dict") else vars(key_detail),
        }

    # ---------------------------------------------------------------------------
    # Storage & Database Health
    # ---------------------------------------------------------------------------

    def export_database_backup(self, backup_dir: Optional[str] = None) -> str:
        """Create a point-in-time backup snapshot of the subscriptions database."""
        return self.sub_manager.export_backup(backup_dir=backup_dir)

    def database_health(self) -> Dict[str, Any]:
        """Validate database integrity and return diagnostic status."""
        return self.sub_manager.validate_database_integrity()

    # ---------------------------------------------------------------------------
    # 💰 Monetization, Stripe Payments & Churn Tracking
    # ---------------------------------------------------------------------------

    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Retrieve high-level monetization KPIs, churn rates, active and churned users."""
        return self.sub_manager.get_churn_and_usage_dashboard()

    def create_checkout_session(
        self,
        tier_id: str = "pro",
        billing_cycle: str = "monthly",
        amount_usd: Optional[float] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a Stripe Checkout session or sandbox link for payment."""
        from ..billing.gateways import PaymentGatewayService
        user = self.sub_manager.get_user(self.user_id)
        email = user.email if user else None
        if amount_usd is None:
            try:
                cfg = get_tier_config(CloudTier(tier_id.lower()))
                amount_usd = cfg.price_yearly_usd if billing_cycle == "yearly" else cfg.price_monthly_usd
            except Exception:
                amount_usd = 19.99
        return PaymentGatewayService.create_checkout_session(
            user_id=self.user_id,
            tier_id=tier_id,
            amount_usd=amount_usd,
            billing_cycle=billing_cycle,
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url
        )

    def create_payment_link(
        self,
        amount_usd: float,
        description: str = "TruthGPT Cloud Service Charge"
    ) -> Dict[str, Any]:
        """Generate an immediate shareable payment link."""
        from ..billing.gateways import PaymentGatewayService
        return PaymentGatewayService.create_payment_link(
            amount_usd=amount_usd,
            description=description,
            user_id=self.user_id
        )

    def cancel_subscription(
        self,
        reason: str = "Usuario canceló suscripción",
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel subscription, recording churn reason and status."""
        return self.sub_manager.cancel_subscription(
            user_id=self.user_id,
            reason=reason,
            feedback=feedback
        )

    def reactivate_subscription(
        self,
        target_tier: Optional[Union[str, CloudTier]] = None
    ) -> Dict[str, Any]:
        """Reactivate canceled/churned user back to active status."""
        return self.sub_manager.reactivate_subscription(
            user_id=self.user_id,
            target_tier=target_tier
        )

    def get_payment_gateway_status(self) -> Dict[str, Any]:
        """Check payment gateway configuration (Stripe, Crypto, Wire)."""
        from ..billing.gateways import PaymentGatewayService
        return PaymentGatewayService.get_gateway_status()
