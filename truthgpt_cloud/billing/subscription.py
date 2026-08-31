"""
💳 TruthGPT Cloud - Subscription Manager & Token Accounting
Manages user accounts, tier entitlements, token quotas, invoices, and API key lifecycles.
"""

import os
import time
import uuid
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

from ..core.tiers import CloudTier, TierConfig, get_tier_config
from ..core.exceptions import (
    QuotaExceededError,
    TierUnauthorizedError,
    AuthenticationError,
    TruthGPTCloudError,
)
from .models import UsageRecord, Invoice, ApiKeyInfo, WebhookSubscription, UserSubscription
from .storage import AtomicJsonStorage
from .gateways import PaymentGatewayService

logger = logging.getLogger("TruthGPT.CloudBilling")


class SubscriptionManager:
    """
    Centralized subscription, accounting, and quota manager for TruthGPT Cloud.
    Persists data in atomic storage for reliability across worker processes.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(base_dir)
            storage_path = os.path.join(parent_dir, "cloud_subscriptions_db.json")
        self.storage_path = storage_path
        self._storage = AtomicJsonStorage(storage_path)
        self._users: Dict[str, UserSubscription] = {}
        self._api_key_to_user: Dict[str, str] = {}
        self._load_storage()

    def _load_storage(self) -> None:
        """Load persistent subscription records and initialize demo users if needed."""
        raw_data = self._storage.load()
        if raw_data:
            for uid, udata in raw_data.items():
                usage_dict = udata.get("usage", {})
                usage = UsageRecord(**usage_dict) if usage_dict else UsageRecord()
                invoices = [Invoice(**inv) for inv in udata.get("invoices", [])]
                tier_val = CloudTier(udata.get("tier", "free"))
                user = UserSubscription(
                    user_id=udata["user_id"],
                    email=udata.get("email", ""),
                    name=udata.get("name", "TruthGPT User"),
                    tier=tier_val,
                    billing_cycle=udata.get("billing_cycle", "monthly"),
                    status=udata.get("status", "active"),
                    api_keys=udata.get("api_keys", []),
                    subscription_start_date=udata.get("subscription_start_date", ""),
                    next_billing_date=udata.get("next_billing_date", ""),
                    usage=usage,
                    invoices=invoices,
                    custom_limits=udata.get("custom_limits")
                )
                self._users[uid] = user
                for key in user.api_keys:
                    self._api_key_to_user[key] = uid

        self._ensure_demo_users()

    def _save_storage(self) -> None:
        """Save subscription records to atomic disk storage."""
        raw_data = {}
        for uid, user in self._users.items():
            data = asdict(user)
            data["tier"] = user.tier.value
            raw_data[uid] = data
        self._storage.save(raw_data)

    def _ensure_demo_users(self) -> None:
        """Guarantee core default users exist in state."""
        demo_accounts = [
            ("usr_default_demo", "demo@truthgpt.ai", "TruthGPT Explorer", CloudTier.FREE),
            ("usr_pro_sample", "researcher@frontier.ai", "Dr. Alexander Truth", CloudTier.PRO),
            ("usr_ultra_enterprise", "singularity@quantum.io", "Enterprise Sovereign", CloudTier.ULTRA),
        ]
        modified = False
        for uid, email, name, tier in demo_accounts:
            if uid not in self._users:
                api_key = f"tgpt_cloud_live_{uuid.uuid4().hex[:16]}"
                user = UserSubscription(
                    user_id=uid,
                    email=email,
                    name=name,
                    tier=tier,
                    api_keys=[api_key],
                    usage=UsageRecord()
                )
                self._users[uid] = user
                self._api_key_to_user[api_key] = uid
                modified = True
        if modified:
            self._save_storage()

    def register_user(self, email: str, name: str, tier: Union[CloudTier, str] = CloudTier.FREE) -> UserSubscription:
        """Register a new user in TruthGPT Cloud with an initial API key."""
        if isinstance(tier, str):
            try:
                tier = CloudTier(tier.lower())
            except ValueError:
                tier = CloudTier.FREE

        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        api_key = f"tgpt_cloud_live_{uuid.uuid4().hex[:20]}"
        
        user = UserSubscription(
            user_id=user_id,
            email=email,
            name=name,
            tier=tier,
            api_keys=[api_key],
            usage=UsageRecord()
        )
        self._users[user_id] = user
        self._api_key_to_user[api_key] = user_id
        self._save_storage()
        return user

    def get_user(self, user_id: str) -> Optional[UserSubscription]:
        """Retrieve user by user_id."""
        return self._users.get(user_id)

    def get_user_by_api_key(self, api_key: str) -> Optional[UserSubscription]:
        """Resolve user subscription from an API key."""
        user_id = self._api_key_to_user.get(api_key)
        if user_id:
            return self.get_user(user_id)
        return None

    def generate_new_api_key(
        self,
        user_id: str,
        label: str = "Default Key",
        scopes: Optional[List[str]] = None
    ) -> str:
        """Generate a new dedicated API key for user, subject to tier limits."""
        user = self.get_user(user_id)
        if not user:
            raise AuthenticationError(f"Usuario {user_id} no encontrado.")
            
        tier_cfg = get_tier_config(user.tier)
        if len(user.api_keys) >= tier_cfg.dedicated_api_keys:
            raise TierUnauthorizedError(
                required_tier="pro" if user.tier == CloudTier.FREE else "ultra",
                current_tier=user.tier.value,
                feature=f"Límite de {tier_cfg.dedicated_api_keys} claves de API alcanzado"
            )
            
        new_key = f"tgpt_cloud_live_{uuid.uuid4().hex[:24]}"
        actual_scopes = scopes or ["inference", "verify", "swarm", "read"]
        if hasattr(user, "api_keys_detail") and user.api_keys_detail is not None:
            user.api_keys_detail.append(ApiKeyInfo(key=new_key, label=label, scopes=actual_scopes))
        user.api_keys.append(new_key)
        self._api_key_to_user[new_key] = user_id
        self._save_storage()
        return new_key

    def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke an active API key."""
        user = self.get_user(user_id)
        if not user or api_key not in user.api_keys:
            return False
        user.api_keys.remove(api_key)
        if api_key in self._api_key_to_user:
            del self._api_key_to_user[api_key]
        self._save_storage()
        return True

    def upgrade_subscription(
        self,
        user_id: str,
        target_tier: Union[CloudTier, str],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """Upgrade or modify subscription tier and create invoice."""
        user = self.get_user(user_id)
        if not user:
            raise AuthenticationError(f"Usuario {user_id} no encontrado.")

        if isinstance(target_tier, str):
            target_tier = CloudTier(target_tier.lower())

        target_cfg = get_tier_config(target_tier)
        amount = target_cfg.price_yearly_usd if billing_cycle == "yearly" else target_cfg.price_monthly_usd
        
        # Process payment gateway
        payment_res = PaymentGatewayService.process_payment(
            user_id=user_id,
            amount_usd=amount,
            tier_id=target_tier.value,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )
        
        # Create invoice record
        invoice = Invoice(
            invoice_id=payment_res["invoice_id"],
            user_id=user_id,
            tier_id=target_tier.value,
            amount_usd=amount,
            billing_cycle=billing_cycle,
            payment_method=payment_method,
            status="paid",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Update user tier & reset daily limit
        user.tier = target_tier
        user.billing_cycle = billing_cycle
        user.status = "active"
        user.invoices.insert(0, invoice)
        user.usage.tokens_consumed_today = 0
        user.usage.daily_request_count = 0
        
        self._save_storage()
        
        return {
            "success": True,
            "message": f"¡Suscripción actualizada exitosamente a {target_cfg.name}!",
            "user_id": user_id,
            "tier": target_tier.value,
            "new_tier": target_tier.value,
            "tier_name": target_cfg.name,
            "invoice": asdict(invoice),
            "payment_details": payment_res,
            "limits": {
                "daily_token_limit": target_cfg.daily_token_limit,
                "context_window": target_cfg.context_window_tokens,
                "max_swarm_agents": target_cfg.max_swarm_agents,
                "verification_level": f"Nivel {target_cfg.smt_z3_verification_depth}",
                "latency_tier": target_cfg.latency_tier
            }
        }

    def check_and_record_quota(
        self,
        user_id: str,
        estimated_tokens: int = 500,
        is_verification: bool = False,
        is_swarm: bool = False
    ) -> bool:
        """Verify that user has enough daily quota and record token usage."""
        user = self.get_user(user_id)
        if not user:
            user = self.get_user_by_api_key(user_id)
        if not user:
            user = self.get_user("usr_default_demo")
        if not user:
            self._ensure_demo_users()
            user = self.get_user("usr_default_demo")
            
        tier_cfg = get_tier_config(user.tier if user else CloudTier.FREE)
        
        # Check daily reset (every 24 hours)
        now = time.time()
        if user and (now - user.usage.last_reset_timestamp > 86400):
            user.usage.tokens_consumed_today = 0
            user.usage.daily_request_count = 0
            user.usage.last_reset_timestamp = now
            
        # Check token quota
        if user and (user.usage.tokens_consumed_today + estimated_tokens > tier_cfg.daily_token_limit):
            raise QuotaExceededError(
                message=(
                    f"Límite diario de tokens alcanzado ({user.usage.tokens_consumed_today}/{tier_cfg.daily_token_limit}). "
                    f"Actualiza tu suscripción a TruthGPT Pro o Ultra para continuar sin interrupciones."
                ),
                limit=tier_cfg.daily_token_limit,
                consumed=user.usage.tokens_consumed_today
            )
        
        # Record consumption
        if user:
            user.usage.total_tokens_consumed += estimated_tokens
            user.usage.tokens_consumed_today += estimated_tokens
            user.usage.daily_request_count += 1
            
            if is_verification:
                user.usage.verifications_run += 1
            if is_swarm:
                user.usage.swarm_sessions_count += 1
                
            self._save_storage()
        return True

    def get_user_status_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive usage, tier, and remaining quota metrics for user."""
        user = self.get_user(user_id)
        if not user:
            user = self.get_user_by_api_key(user_id)
        if not user:
            user = self.get_user("usr_default_demo")
        if not user:
            if self._users:
                user = next(iter(self._users.values()))
            else:
                self._ensure_demo_users()
                user = self.get_user("usr_default_demo") or UserSubscription(
                    user_id="usr_fallback",
                    email="fallback@truthgpt.ai",
                    name="TruthGPT User",
                    tier=CloudTier.FREE,
                    api_keys=["tgpt_cloud_demo_key"]
                )
            
        tier_cfg = get_tier_config(user.tier)
        remaining_tokens = max(0, tier_cfg.daily_token_limit - user.usage.tokens_consumed_today)
        pct_used = min(100.0, (user.usage.tokens_consumed_today / max(1, tier_cfg.daily_token_limit)) * 100)
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "tier": user.tier.value,
            "tier_name": tier_cfg.name,
            "tier_badge": tier_cfg.badge,
            "billing_cycle": user.billing_cycle,
            "status": user.status,
            "api_keys": user.api_keys,
            "metrics": {
                "tokens_consumed_today": user.usage.tokens_consumed_today,
                "daily_token_limit": tier_cfg.daily_token_limit,
                "remaining_tokens": remaining_tokens,
                "percent_quota_used": round(pct_used, 1),
                "total_tokens_all_time": user.usage.total_tokens_consumed,
                "verifications_completed": user.usage.verifications_run,
                "swarm_runs": user.usage.swarm_sessions_count,
                "requests_today": user.usage.daily_request_count
            },
            "features": {
                "context_window": tier_cfg.context_window_tokens,
                "max_swarm_agents": tier_cfg.max_swarm_agents,
                "smt_verification_depth": tier_cfg.smt_z3_verification_depth,
                "proof_certificates": tier_cfg.proof_certificate_generation,
                "latency_tier": tier_cfg.latency_tier,
                "models": tier_cfg.available_models
            },
            "recent_invoices": [asdict(inv) for inv in user.invoices[:5]],
            "invoices": [asdict(inv) for inv in user.invoices]
        }


# Global singleton instance
subscription_manager = SubscriptionManager()

__all__ = [
    "UsageRecord",
    "Invoice",
    "ApiKeyInfo",
    "WebhookSubscription",
    "UserSubscription",
    "SubscriptionManager",
    "subscription_manager",
]
