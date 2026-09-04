"""
💳 TruthGPT Cloud - Subscription Manager & Token Accounting
Manages user accounts, tier entitlements, token quotas, invoices, and API key lifecycles.
"""

import os
import sys
import shutil
import tempfile
import time
import uuid
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

from ..core.tiers import CloudTier, get_tier_config
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

TOKEN_PACK_CATALOG: List[Dict[str, Any]] = [
    {
        "pack_id": "pack_starter",
        "name": "Starter Boost Pack",
        "tokens": 500_000,
        "price_usd": 5.00,
        "description": "500,000 tokens adicionales para picos de inferencia y verificación SMT."
    },
    {
        "pack_id": "pack_pro",
        "name": "Pro Research Pack",
        "tokens": 2_500_000,
        "price_usd": 19.00,
        "description": "2,500,000 tokens adicionales con prioridad de cómputo."
    },
    {
        "pack_id": "pack_scale",
        "name": "Scale Enterprise Pack",
        "tokens": 10_000_000,
        "price_usd": 65.00,
        "description": "10,000,000 tokens para despliegues a gran escala y swarms paralelos."
    },
    {
        "pack_id": "pack_enterprise",
        "name": "Frontier Ultra Pack",
        "tokens": 50_000_000,
        "price_usd": 250.00,
        "description": "50,000,000 tokens para cargas masivas con SLA dedicado."
    }
]


class SubscriptionManager:
    """
    Centralized subscription, accounting, and quota manager for TruthGPT Cloud.
    Persists data in atomic storage for reliability across worker processes.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = os.environ.get("TRUTHGPT_STORAGE_PATH")
            if not storage_path:
                main_file = sys.argv[0] if sys.argv else ""
                is_testing = (
                    "PYTEST_CURRENT_TEST" in os.environ
                    or "pytest" in sys.modules
                    or "test_" in os.path.basename(main_file).lower()
                    or os.path.basename(main_file).lower().startswith("test")
                )
                if is_testing:
                    test_dir = os.path.join(tempfile.gettempdir(), "truthgpt_test_storage")
                    os.makedirs(test_dir, exist_ok=True)
                    storage_path = os.path.join(test_dir, "cloud_subscriptions_test.json")
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    parent_dir = os.path.dirname(base_dir)
                    orig = os.path.join(parent_dir, "cloud_subscriptions_db.json")
                    if os.path.exists(orig) and not os.path.exists(storage_path):
                        shutil.copy2(orig, storage_path)
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    parent_dir = os.path.dirname(base_dir)
                    storage_path = os.path.join(parent_dir, "cloud_subscriptions_db.json")
        self.storage_path = storage_path
        self._storage = AtomicJsonStorage(storage_path)
        self._users: Dict[str, UserSubscription] = {}
        self._api_key_to_user: Dict[str, str] = {}
        self._load_storage()

    @property
    def storage(self) -> AtomicJsonStorage:
        """Expose underlying atomic JSON storage backend."""
        return self._storage

    def _load_storage(self) -> None:
        """Load persistent subscription records and initialize demo users if needed."""
        raw_data = self._storage.load()
        if raw_data:
            for uid, udata in raw_data.items():
                usage_dict = udata.get("usage", {})
                usage = UsageRecord(**usage_dict) if usage_dict else UsageRecord()
                invoices = [Invoice(**inv) for inv in udata.get("invoices", [])]
                tier_val = CloudTier(udata.get("tier", "free"))

                # Load api keys detail if present
                api_details = [
                    ApiKeyInfo(**d) for d in udata.get("api_key_details", udata.get("api_keys_detail", []))
                ]

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
                    api_key_details=api_details,
                    custom_limits=udata.get("custom_limits")
                )
                self._users[uid] = user
                for key in user.api_keys:
                    self._api_key_to_user[key] = uid

        self._ensure_demo_users()
        self._sync_security_registry()

    def _sync_security_registry(self) -> None:
        """Synchronize loaded user API keys into the cryptographic security registry."""
        try:
            from ..security import cloud_security
            for uid, user in self._users.items():
                for key in user.api_keys:
                    cloud_security.register_existing_key(
                        raw_key=key,
                        user_id=uid,
                        name=f"{user.name} Key"
                    )
        except Exception as e:
            logger.debug(f"Security sync note: {e}")

    def _save_storage(self) -> None:
        """Save subscription records to atomic disk storage."""
        raw_data = {}
        for uid, user in self._users.items():
            data = user.to_dict()
            raw_data[uid] = data
        self._storage.save(raw_data)

    def _ensure_demo_users(self) -> None:
        """Guarantee core default users exist in state."""
        demo_accounts = [
            ("usr_default_demo", "demo@truthgpt.ai", "TruthGPT Explorer", CloudTier.FREE),
            ("usr_pro_sample", "researcher@frontier.ai", "Dr. Alexander Truth", CloudTier.PRO),
            ("usr_ultra_enterprise", "singularity@quantum.io", "Enterprise Sovereign", CloudTier.ULTRA),
            ("usr_enterprise_sample", "enterprise@truthgpt.ai", "TruthGPT Enterprise Corp", CloudTier.ENTERPRISE),
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

    def register_user(
        self,
        email: str,
        name: str,
        tier: Union[CloudTier, str] = CloudTier.FREE
    ) -> UserSubscription:
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

        try:
            from ..security import cloud_security
            cloud_security.register_existing_key(
                raw_key=api_key,
                user_id=user_id,
                name=f"{name} Primary Key"
            )
            from ..telemetry import cloud_telemetry
            cloud_telemetry.record_audit_event("signup", user_id, {"email": email, "tier": user.tier.value})
        except Exception:
            pass

        return user

    def get_user(self, user_id: str) -> Optional[UserSubscription]:
        """Retrieve user by user_id."""
        return self._users.get(user_id)

    get_subscription = get_user

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

        if hasattr(user, "api_key_details"):
            user.api_key_details.append(
                ApiKeyInfo(key=new_key, key_id=f"key_{uuid.uuid4().hex[:8]}", label=label, scopes=actual_scopes)
            )
        user.api_keys.append(new_key)
        self._api_key_to_user[new_key] = user_id
        self._save_storage()

        try:
            from ..security import cloud_security, ApiKeyScope
            scope_enums = {ApiKeyScope(s) for s in actual_scopes if s in ApiKeyScope._value2member_map_}
            cloud_security.register_existing_key(
                raw_key=new_key,
                user_id=user_id,
                name=label,
                scopes=scope_enums or None
            )
            from ..telemetry import cloud_telemetry
            cloud_telemetry.record_audit_event("key_generated", user_id, {"label": label, "scopes": actual_scopes})
        except Exception:
            pass

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

        try:
            from ..security import cloud_security
            h = cloud_security.hash_key(api_key)
            cloud_security.revoke_key(h)
            from ..telemetry import cloud_telemetry
            cloud_telemetry.record_audit_event("key_revoked", user_id, {"key_prefix": api_key[:16] + "..."})
        except Exception:
            pass

        return True

    def upgrade_subscription(
        self,
        user_id: str,
        target_tier: Union[CloudTier, str],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card",
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upgrade or modify subscription tier, applying optional promo codes, and create invoice."""
        user = self.get_user(user_id)
        if not user:
            raise AuthenticationError(f"Usuario {user_id} no encontrado.")

        if isinstance(target_tier, str):
            target_tier = CloudTier(target_tier.lower())

        target_cfg = get_tier_config(target_tier)
        base_amount = target_cfg.price_yearly_usd if billing_cycle == "yearly" else target_cfg.price_monthly_usd

        # Apply promo code discount if provided
        discount_usd = 0.0
        applied_promo = None
        if promo_code:
            code_clean = promo_code.strip().upper()
            if code_clean == "TRUTH2026":
                discount_usd = round(base_amount * 0.20, 2)
                applied_promo = code_clean
            elif code_clean == "DEV50":
                discount_usd = round(base_amount * 0.50, 2)
                applied_promo = code_clean
            elif code_clean in ["SINGULARITY100", "FREE100"]:
                discount_usd = base_amount
                applied_promo = code_clean

        final_amount = max(0.0, round(base_amount - discount_usd, 2))

        # Process payment gateway
        payment_res = PaymentGatewayService.process_payment(
            user_id=user_id,
            amount_usd=final_amount,
            tier_id=target_tier.value,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )

        # Create invoice record
        invoice = Invoice(
            invoice_id=payment_res["invoice_id"],
            user_id=user_id,
            tier_id=target_tier.value,
            amount_usd=final_amount,
            billing_cycle=billing_cycle,
            payment_method=payment_method,
            status="paid",
            discount_applied_usd=discount_usd,
            promo_code=applied_promo,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Update user tier & reset daily limit
        user.tier = target_tier
        user.billing_cycle = billing_cycle
        user.status = "active"
        user.invoices.insert(0, invoice)
        user.usage.tokens_consumed_today = 0
        self._save_storage()

        try:
            from ..telemetry import cloud_telemetry
            cloud_telemetry.record_audit_event(
                "subscription_upgraded",
                user_id,
                {"tier": target_tier.value, "amount_usd": final_amount, "discount_usd": discount_usd, "billing_cycle": billing_cycle}
            )
            from .webhooks import webhook_manager
            webhook_manager.emit_event(
                "subscription.upgraded",
                user_id,
                {"new_tier": target_tier.value, "amount_usd": final_amount, "invoice_id": invoice.invoice_id}
            )
        except Exception:
            pass

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

    def get_token_pack_catalog(self) -> List[Dict[str, Any]]:
        """Return the official catalog of top-up token packs."""
        return [dict(p) for p in TOKEN_PACK_CATALOG]

    def purchase_token_pack(
        self,
        user_id: str,
        pack_id: str,
        payment_method: str = "stripe_card",
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase on-demand top-up tokens for bursts of inference and formal proofs without tier modification.
        """
        user = self.get_user(user_id)
        if not user:
            user = self.get_user_by_api_key(user_id)
        if not user:
            raise AuthenticationError(f"Usuario {user_id} no encontrado.")

        pack = next((p for p in TOKEN_PACK_CATALOG if p["pack_id"] == pack_id), None)
        if not pack:
            valid_ids = [p["pack_id"] for p in TOKEN_PACK_CATALOG]
            raise TruthGPTCloudError(
                f"Paquete de tokens '{pack_id}' no válido. Opciones: {', '.join(valid_ids)}",
                code="INVALID_PACK",
                status_code=400
            )

        base_amount = pack["price_usd"]
        discount_usd = 0.0
        applied_promo = None
        if promo_code:
            code_clean = promo_code.strip().upper()
            if code_clean == "TRUTH2026":
                discount_usd = round(base_amount * 0.20, 2)
                applied_promo = code_clean
            elif code_clean == "DEV50":
                discount_usd = round(base_amount * 0.50, 2)
                applied_promo = code_clean
            elif code_clean in ["SINGULARITY100", "FREE100"]:
                discount_usd = base_amount
                applied_promo = code_clean

        final_amount = max(0.0, round(base_amount - discount_usd, 2))

        # Process payment gateway
        payment_res = PaymentGatewayService.process_payment(
            user_id=user.user_id,
            amount_usd=final_amount,
            tier_id=f"topup_{pack_id}",
            billing_cycle="one_time",
            payment_method=payment_method
        )

        # Create invoice record
        invoice = Invoice(
            invoice_id=payment_res["invoice_id"],
            user_id=user.user_id,
            tier_id=f"topup_{pack_id}",
            amount_usd=final_amount,
            billing_cycle="one_time",
            payment_method=payment_method,
            status="paid",
            discount_applied_usd=discount_usd,
            promo_code=applied_promo,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Increment purchased tokens balances
        current_purchased = getattr(user.usage, "purchased_tokens_balance", 0)
        total_purchased = getattr(user.usage, "total_purchased_tokens", 0)
        user.usage.purchased_tokens_balance = current_purchased + pack["tokens"]
        user.usage.total_purchased_tokens = total_purchased + pack["tokens"]
        user.invoices.insert(0, invoice)
        self._save_storage()

        try:
            from ..telemetry import cloud_telemetry
            cloud_telemetry.record_audit_event(
                "token_pack_purchased",
                user.user_id,
                {"pack_id": pack_id, "tokens_added": pack["tokens"], "amount_usd": final_amount, "new_balance": user.usage.purchased_tokens_balance}
            )
            from .webhooks import webhook_manager
            webhook_manager.emit_event(
                "subscription.top_up",
                user.user_id,
                {"pack_id": pack_id, "tokens_added": pack["tokens"], "new_balance": user.usage.purchased_tokens_balance, "invoice_id": invoice.invoice_id}
            )
        except Exception:
            pass

        return {
            "success": True,
            "message": f"¡Paquete {pack['name']} adquirido con éxito! Se han sumado {pack['tokens']:,} tokens a tu saldo.",
            "user_id": user.user_id,
            "pack_id": pack_id,
            "pack_name": pack["name"],
            "tokens_added": pack["tokens"],
            "new_purchased_balance": user.usage.purchased_tokens_balance,
            "invoice": asdict(invoice),
            "payment_details": payment_res
        }

    def check_and_record_quota(
        self,
        user_id: str,
        estimated_tokens: int = 500,
        is_verification: bool = False,
        is_swarm: bool = False
    ) -> bool:
        """Verify that user has enough quota (daily or purchased top-up balance) and record token usage."""
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

        # Check token quota: daily quota + purchased top-up balance
        if user:
            daily_remaining = max(0, tier_cfg.daily_token_limit - user.usage.tokens_consumed_today)
            purchased_balance = getattr(user.usage, "purchased_tokens_balance", 0)
            total_available = daily_remaining + purchased_balance

            if estimated_tokens > total_available:
                try:
                    from .webhooks import webhook_manager
                    webhook_manager.emit_event("quota.exceeded", user.user_id, {
                        "consumed": user.usage.tokens_consumed_today,
                        "limit": tier_cfg.daily_token_limit,
                        "purchased_balance": purchased_balance,
                        "requested_tokens": estimated_tokens
                    })
                except Exception:
                    pass
                raise QuotaExceededError(
                    message=(
                        f"Límite de tokens superado ({user.usage.tokens_consumed_today}/{tier_cfg.daily_token_limit}, saldo adicional: {purchased_balance:,}). "
                        f"Adquiere un paquete de tokens adicional (top-up) o actualiza tu suscripción a TruthGPT Pro o Ultra."
                    ),
                    limit=tier_cfg.daily_token_limit,
                    consumed=user.usage.tokens_consumed_today
                )

        # Record consumption
        if user:
            prev_pct = (user.usage.tokens_consumed_today / max(1, tier_cfg.daily_token_limit))

            # Consume from daily limit first, then from purchased balance
            if user.usage.tokens_consumed_today < tier_cfg.daily_token_limit:
                daily_fill = min(estimated_tokens, tier_cfg.daily_token_limit - user.usage.tokens_consumed_today)
                user.usage.tokens_consumed_today += daily_fill
                excess = estimated_tokens - daily_fill
            else:
                excess = estimated_tokens

            if excess > 0:
                current_purchased = getattr(user.usage, "purchased_tokens_balance", 0)
                user.usage.purchased_tokens_balance = max(0, current_purchased - excess)

            user.usage.total_tokens_consumed += estimated_tokens
            user.usage.daily_request_count += 1
            new_pct = (user.usage.tokens_consumed_today / max(1, tier_cfg.daily_token_limit))

            # Trigger warning event if 80% threshold crossed
            if prev_pct < 0.8 <= new_pct:
                try:
                    from .webhooks import webhook_manager
                    webhook_manager.emit_event("quota.warning", user.user_id, {
                        "consumed": user.usage.tokens_consumed_today,
                        "limit": tier_cfg.daily_token_limit,
                        "percentage": round(new_pct * 100, 1)
                    })
                except Exception:
                    pass

            if is_verification:
                user.usage.verifications_run += 1
            if is_swarm:
                user.usage.swarm_sessions_count += 1

            self._save_storage()
        return True


    def get_user_status_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive usage, tier, purchased balance, and remaining quota metrics for user."""
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
        remaining_daily = max(0, tier_cfg.daily_token_limit - user.usage.tokens_consumed_today)
        purchased_balance = getattr(user.usage, "purchased_tokens_balance", 0)
        total_available = remaining_daily + purchased_balance
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
                "remaining_tokens": remaining_daily,
                "remaining_daily_tokens": remaining_daily,
                "purchased_tokens_balance": purchased_balance,
                "total_available_tokens": total_available,
                "percent_quota_used": round(pct_used, 1),
                "total_tokens_all_time": user.usage.total_tokens_consumed,
                "total_purchased_tokens": getattr(user.usage, "total_purchased_tokens", 0),
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


    def get_usage_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Generate detailed telemetry analytics and cost breakdown for user.
        """
        summary = self.get_user_status_summary(user_id)
        m = summary["metrics"]

        # Breakdown estimations
        prompt_tokens = int(m["total_tokens_all_time"] * 0.4)
        completion_tokens = int(m["total_tokens_all_time"] * 0.6)

        return {
            "user_id": user_id,
            "tier": summary["tier"],
            "tier_name": summary["tier_name"],
            "period": "current_billing_cycle",
            "tokens": {
                "total": m["total_tokens_all_time"],
                "today": m["tokens_consumed_today"],
                "remaining_today": m["remaining_tokens"],
                "estimated_prompt_tokens": prompt_tokens,
                "estimated_completion_tokens": completion_tokens,
                "daily_limit": m["daily_token_limit"]
            },
            "operations": {
                "formal_verifications": m["verifications_completed"],
                "swarm_sessions": m["swarm_runs"],
                "daily_requests": m["requests_today"]
            },
            "efficiency": {
                "quota_utilization_pct": m["percent_quota_used"],
                "cache_hit_savings_estimated_usd": round(m["verifications_completed"] * 0.002, 4)
            },
            "active_api_keys_count": len(summary["api_keys"]),
            "invoices_count": len(summary["invoices"])
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
