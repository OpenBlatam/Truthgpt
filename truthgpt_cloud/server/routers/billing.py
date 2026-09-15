"""
💳 TruthGPT Cloud Server - Billing & Subscription Router
Handles tiers, user signups, subscription upgrades, API keys, promos, webhooks, and storage maintenance.
"""

import os
import hmac
import hashlib
import logging
from dataclasses import asdict
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger("TruthGPT.CloudServerBilling")

from ..models import (
    UserAuthRequest,
    UpgradeRequest,
    IssueTokenRequest,
    ApplyPromoRequest,
    WebhookRegisterRequest,
    WebhookTestTriggerRequest,
    WebhookVerifyRequest,
    CheckoutSessionRequest,
    PaymentLinkRequest,
    PortalSessionRequest,
    DirectChargeRequest,
    CancelSubscriptionRequest,
    ReactivateSubscriptionRequest,
    BillingConfigUpdateRequest,
    CheckoutCompleteRequest,
)
from ..dependencies import resolve_user
from ...core.tiers import CloudTier, get_all_tiers, get_tier_config
from ...billing.subscription import subscription_manager
from ...billing.gateways import PaymentGatewayService
from ...billing.webhooks import webhook_manager
from ...rate_limiting import token_bucket_limiter
from ...security.manager import create_session_jwt
from ..dashboard_html import get_dashboard_html

router = APIRouter(tags=["Billing & Subscriptions"])


@router.post("/api/v1/cloud/billing/config")
async def update_billing_config_endpoint(req: BillingConfigUpdateRequest):
    """Update Stripe credentials dynamically in memory and persist to .env."""
    status = PaymentGatewayService.update_stripe_credentials(
        secret_key=req.stripe_secret_key,
        publishable_key=req.stripe_publishable_key,
        webhook_secret=req.stripe_webhook_secret,
        persist_to_env=True
    )
    test_res = None
    if req.test_after_save and req.stripe_secret_key:
        test_res = PaymentGatewayService.test_stripe_connection()
    return {
        "success": True,
        "message": "Credenciales de pasarela actualizadas exitosamente.",
        "gateways": status,
        "test_connection": test_res
    }


@router.get("/api/v1/cloud/billing/test-connection")
async def test_stripe_connection_endpoint():
    """Test connection with Stripe API using currently configured STRIPE_SECRET_KEY."""
    return PaymentGatewayService.test_stripe_connection()


@router.post("/api/v1/cloud/billing/checkout/complete")
async def complete_checkout_endpoint(req: CheckoutCompleteRequest):
    """
    Complete an interactive checkout payment (Sandbox or Stripe payment link confirmation).
    Registers the paid invoice, upgrades the user's tier, and updates MRR/ARR analytics immediately.
    """
    try:
        tier_enum = CloudTier(req.tier_id.lower())
    except Exception:
        tier_enum = CloudTier.PRO

    user = subscription_manager.get_user(req.user_id) or subscription_manager.get_user_by_api_key(req.user_id)
    if not user:
        email = req.customer_email or f"{req.user_id}@truthgpt.ai"
        name = req.customer_name or f"Cliente {req.user_id}"
        user = subscription_manager.register_user(email=email, name=name, tier=tier_enum)

    desc = req.description or f"TruthGPT Cloud {tier_enum.value.upper()} ({req.billing_cycle or 'mensual'})"
    charge_res = subscription_manager.charge_user(
        user_id=user.user_id,
        amount_usd=req.amount_usd,
        description=desc,
        payment_method=req.payment_method or "stripe_card"
    )

    if user.tier != tier_enum:
        subscription_manager.upgrade_subscription(
            user_id=user.user_id,
            target_tier=tier_enum,
            billing_cycle=req.billing_cycle or "monthly",
            payment_method=req.payment_method or "stripe_card"
        )

    subscription_manager.record_activity(user.user_id)

    return {
        "success": True,
        "message": f"¡Pago de ${req.amount_usd:.2f} USD completado con éxito! Suscripción activada.",
        "invoice": charge_res.get("invoice"),
        "user_id": user.user_id,
        "tier": user.tier.value,
        "api_key": user.api_keys[0] if user.api_keys else None
    }


@router.get("/api/v1/cloud/tiers")
async def list_tiers():
    """Retrieve all available subscription plans and comparison matrix."""
    return {
        "success": True,
        "tiers": get_all_tiers(),
        "gemini_comparison": {
            "truthgpt_pro_vs_gemini_advanced": "TruthGPT Pro includes Z3 SMT Mathematical Verification & DbC Contracts not present in Gemini Advanced.",
            "truthgpt_ultra_vs_gemini_ultra": "TruthGPT Ultra features Quantum Consensus Ensemble across multiple frontier LLMs + 2M context + Zero-Queue inference."
        }
    }


@router.post("/api/v1/auth/token")
async def issue_token(req: IssueTokenRequest):
    """Mint a stateless JWT session token for user authentication."""
    try:
        token = create_session_jwt(
            user_id=req.user_id,
            tier=req.tier or "pro",
            scopes=req.scopes,
            expires_in_seconds=req.expires_in_seconds or 3600,
        )
        return {
            "success": True,
            "token_type": "Bearer",
            "access_token": token,
            "expires_in": req.expires_in_seconds or 3600,
            "user_id": req.user_id,
            "tier": req.tier or "pro",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/v1/cloud/auth/signup")
async def signup_user(req: UserAuthRequest):
    """Register a new user in TruthGPT Cloud with API keys."""
    try:
        tier_enum = CloudTier(req.initial_tier.lower())
    except ValueError:
        tier_enum = CloudTier.FREE

    user = subscription_manager.register_user(
        email=req.email,
        name=req.name,
        tier=tier_enum
    )
    return {
        "success": True,
        "user_id": user.user_id,
        "api_key": user.api_keys[0],
        "tier": user.tier.value,
        "message": "User registered successfully in TruthGPT Cloud."
    }


@router.get("/api/v1/cloud/subscription/me")
async def get_subscription(user_id: str = Query("usr_default_demo")):
    """Get current subscription metrics, quotas, token balances and invoices."""
    summary = subscription_manager.get_user_status_summary(user_id)
    return {"success": True, "subscription": summary}


@router.post("/api/v1/cloud/subscription/upgrade")
async def upgrade_tier(req: UpgradeRequest):
    """Upgrade or change user subscription tier (simulating Stripe / Crypto payment)."""
    try:
        tier_enum = CloudTier(req.target_tier.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {req.target_tier}")

    try:
        result = subscription_manager.upgrade_subscription(
            user_id=req.user_id,
            target_tier=tier_enum,
            billing_cycle=req.billing_cycle,
            payment_method=req.payment_method
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/cloud/subscription/generate-key")
async def generate_api_key(user_id: str = Query("usr_default_demo")):
    """Generate a new dedicated API key for user under their tier allotment."""
    try:
        new_key = subscription_manager.generate_new_api_key(user_id)
        return {"success": True, "api_key": new_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/cloud/subscription/revoke-key")
async def revoke_api_key(user_id: str = Query("usr_default_demo"), api_key: str = Query(...)):
    """Revoke an active API key."""
    success = subscription_manager.revoke_api_key(user_id, api_key)
    return {"success": success, "message": "Key revoked" if success else "Key not found"}


@router.post("/api/v1/cloud/subscription/apply-promo")
async def apply_promo_endpoint(req: ApplyPromoRequest):
    """Apply a promo code to upgrade a subscription with discount."""
    return subscription_manager.upgrade_subscription(
        user_id=req.user_id,
        target_tier=req.target_tier,
        billing_cycle=req.billing_cycle or "monthly",
        promo_code=req.promo_code
    )


@router.get("/api/v1/cloud/usage/analytics")
async def get_usage_analytics_endpoint(
    user_id: str = Query("usr_default_demo"),
    auth_user: str = Depends(resolve_user)
):
    """Retrieve detailed token consumption, cost analytics, and operations breakdown."""
    uid = user_id if user_id and user_id != "usr_default_demo" else auth_user
    analytics = subscription_manager.get_usage_analytics(uid)
    return {"success": True, "analytics": analytics}


@router.get("/api/v1/cloud/rate-limits/{user_id}")
async def get_rate_limit_status_endpoint(user_id: str):
    """Retrieve current rate limit status and quota balance for a user."""
    sub = subscription_manager.get_subscription(user_id)
    tier = sub.tier if sub is not None else CloudTier.FREE
    tier_cfg = get_tier_config(tier)
    tokens = token_bucket_limiter.get_user_tokens(user_id, max_capacity=float(tier_cfg.requests_per_minute))
    return {
        "success": True,
        "user_id": user_id,
        "tier": tier_cfg.tier_id.value,
        "requests_per_minute_capacity": tier_cfg.requests_per_minute,
        "available_tokens": round(tokens, 2),
        "is_active": getattr(sub, "is_active", True) if sub is not None else True,
    }


# ---------------------------------------------------------------------------
# 🔔 Webhooks
# ---------------------------------------------------------------------------

@router.get("/api/v1/cloud/webhooks")
async def list_webhooks(user_id: str = Query("usr_default_demo")):
    """List registered webhooks for a user."""
    subs = webhook_manager.list_user_webhooks(user_id)
    return {"success": True, "webhooks": [asdict(s) for s in subs]}


@router.post("/api/v1/cloud/webhooks")
async def register_webhook(req: WebhookRegisterRequest):
    """Register a new developer webhook URL."""
    sub = webhook_manager.register_webhook(req.user_id, req.target_url, req.subscribed_events)
    return {"success": True, "webhook": asdict(sub)}


@router.post("/api/v1/cloud/webhooks/verify")
@router.post("/api/v1/cloud/webhooks/verify-signature")
async def verify_webhook_endpoint(req: WebhookVerifyRequest):
    """Verify the authenticity of a TruthGPT webhook payload signature."""
    is_valid = webhook_manager.verify_webhook_signature(
        payload_data=req.payload,
        signature_header=req.signature,
        secret=req.secret or "tgpt_global_webhook_secret"
    )
    return {"success": True, "is_valid": is_valid, "verified": is_valid}


@router.delete("/api/v1/cloud/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a registered webhook."""
    deleted = webhook_manager.delete_webhook(webhook_id)
    return {"success": deleted, "message": "Webhook deleted" if deleted else "Webhook not found"}


@router.post("/api/v1/cloud/webhooks/test-trigger")
async def test_trigger_webhook(req: WebhookTestTriggerRequest):
    """Emit a test webhook event."""
    evt = webhook_manager.emit_event(req.event_type, req.user_id, req.data or {"message": "Test webhook event"})
    return {"success": True, "event": asdict(evt)}

test_trigger_webhook.__test__ = False


# ---------------------------------------------------------------------------
# 💾 Storage Maintenance & Backup
# ---------------------------------------------------------------------------

@router.post("/api/v1/cloud/storage/maintenance/backup")
async def trigger_storage_backup_endpoint():
    """Trigger point-in-time backup snapshot of the subscriptions database."""
    backup_path = subscription_manager.export_backup()
    return {"success": True, "backup_path": backup_path}


@router.post("/api/v1/cloud/storage/maintenance/compact")
async def trigger_storage_compact_endpoint():
    """Prune inactive API keys and compact the storage backend."""
    res = subscription_manager.compact_database()
    return res


# ---------------------------------------------------------------------------
# 📊 Executive Analytics & Churn Dashboard
# ---------------------------------------------------------------------------

@router.get("/api/v1/cloud/dashboard/overview")
async def get_dashboard_overview():
    """Retrieve comprehensive monetization KPIs, active users, churned users, and revenue metrics."""
    return subscription_manager.get_churn_and_usage_dashboard()


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/admin", response_class=HTMLResponse)
@router.get("/api/v1/cloud/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the TruthGPT Cloud Executive Monetization and Churn Analytics Web Dashboard."""
    return HTMLResponse(content=get_dashboard_html(), status_code=200)


@router.get("/api/v1/cloud/billing/status")
@router.get("/api/v1/cloud/gateways/status")
async def get_gateway_status_endpoint():
    """Check payment gateway configuration (Stripe Live/Test/Sandbox, Crypto, Wire)."""
    return {"success": True, "gateways": PaymentGatewayService.get_gateway_status()}


# ---------------------------------------------------------------------------
# 💳 Live Stripe Checkout, Payment Links & On-Demand Charging
# ---------------------------------------------------------------------------

@router.post("/api/v1/cloud/billing/checkout-session")
async def create_checkout_session_endpoint(req: CheckoutSessionRequest):
    """
    Create a Stripe Checkout session or instant sandbox checkout URL for subscriptions or top-ups.
    """
    user = subscription_manager.get_user(req.user_id) or subscription_manager.get_user_by_api_key(req.user_id)
    email = req.customer_email or (user.email if user else None)

    amount = req.amount_usd
    if amount is None or amount <= 0:
        try:
            tier_enum = CloudTier(req.tier_id.lower())
            cfg = get_tier_config(tier_enum)
            amount = cfg.price_yearly_usd if req.billing_cycle == "yearly" else cfg.price_monthly_usd
        except Exception:
            amount = 19.99

    res = PaymentGatewayService.create_checkout_session(
        user_id=req.user_id,
        tier_id=req.tier_id,
        amount_usd=amount,
        billing_cycle=req.billing_cycle,
        customer_email=email,
        success_url=req.success_url,
        cancel_url=req.cancel_url
    )
    return res


@router.post("/api/v1/cloud/billing/payment-link")
async def create_payment_link_endpoint(req: PaymentLinkRequest):
    """
    Generate an immediate shareable payment link for custom amounts, token packs or enterprise invoices.
    """
    return PaymentGatewayService.create_payment_link(
        amount_usd=req.amount_usd,
        description=req.description,
        user_id=req.user_id
    )


@router.post("/api/v1/cloud/billing/portal-session")
async def create_portal_session_endpoint(req: PortalSessionRequest):
    """Generate a self-service customer billing portal session."""
    user = subscription_manager.get_user(req.user_id) or subscription_manager.get_user_by_api_key(req.user_id)
    cust_id = getattr(user, "stripe_customer_id", None) if user else None
    return PaymentGatewayService.create_customer_portal_session(
        user_id=req.user_id,
        customer_id=cust_id,
        return_url=req.return_url
    )


@router.post("/api/v1/cloud/billing/charge-direct")
async def charge_direct_endpoint(req: DirectChargeRequest):
    """Directly execute a charge and issue a paid invoice for a user."""
    try:
        res = subscription_manager.charge_user(
            user_id=req.user_id,
            amount_usd=req.amount_usd,
            description=req.description or "TruthGPT Cloud Service Charge",
            payment_method=req.payment_method or "stripe_card"
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/cloud/billing/webhook/stripe")
async def stripe_webhook_endpoint(request: Request):
    """
    Process official Stripe webhook events (checkout.session.completed, customer.subscription.deleted, invoice.payment_succeeded, invoice.payment_failed).
    Validates HMAC-SHA256 signature when STRIPE_WEBHOOK_SECRET is configured.
    """
    import json
    try:
        body_bytes = await request.body()

        # Signature verification if secret is configured
        sig_header = request.headers.get("Stripe-Signature")
        wh_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if wh_secret and sig_header:
            try:
                pairs = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
                t = pairs.get("t")
                v1 = pairs.get("v1")
                if t and v1:
                    signed_payload = f"{t}.".encode("utf-8") + body_bytes
                    expected_sig = hmac.new(wh_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(expected_sig, v1):
                        logger.warning("Stripe webhook signature verification failed.")
                        return {"success": False, "error": "Invalid signature"}
            except Exception as sig_err:
                logger.warning(f"Error checking stripe signature: {sig_err}")

        payload_data = {}
        if body_bytes:
            try:
                payload_data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                payload_data = {}

        event_type = payload_data.get("type", "unknown")
        event_obj = (payload_data.get("data") or {}).get("object", {})

        # Handle Checkout Session Completed (Upgrades & Activations)
        if event_type == "checkout.session.completed":
            uid = event_obj.get("client_reference_id") or (event_obj.get("metadata") or {}).get("user_id")
            tier_id = (event_obj.get("metadata") or {}).get("tier_id", "pro")
            cycle = (event_obj.get("metadata") or {}).get("billing_cycle", "monthly")
            cust_id = event_obj.get("customer")
            if uid:
                user = subscription_manager.get_user(uid)
                if user and cust_id:
                    user.stripe_customer_id = cust_id
                subscription_manager.upgrade_subscription(
                    user_id=uid,
                    target_tier=tier_id,
                    billing_cycle=cycle,
                    payment_method="stripe_card"
                )

        # Handle Recurring Payment Succeeded (Renewal & Invoicing)
        elif event_type in ["invoice.payment_succeeded", "invoice.paid", "charge.succeeded"]:
            cust_id = event_obj.get("customer")
            amount_paid = event_obj.get("amount_paid") or event_obj.get("amount")
            amount_usd = (amount_paid / 100.0) if amount_paid else 0.0
            if cust_id:
                for u in subscription_manager._users.values():
                    if getattr(u, "stripe_customer_id", None) == cust_id:
                        if amount_usd > 0:
                            subscription_manager.charge_user(
                                user_id=u.user_id,
                                amount_usd=amount_usd,
                                description="Renovación periódica Stripe",
                                payment_method="stripe_card"
                            )
                        break

        # Handle Payment Failed (Flag At-Risk)
        elif event_type in ["invoice.payment_failed", "charge.failed"]:
            cust_id = event_obj.get("customer")
            if cust_id:
                for u in subscription_manager._users.values():
                    if getattr(u, "stripe_customer_id", None) == cust_id:
                        u.churn_status = "at_risk"
                        subscription_manager._save_storage()
                        break

        # Handle Customer Subscription Deleted (Churn detection!)
        elif event_type in ["customer.subscription.deleted", "customer.subscription.canceled"]:
            cust_id = event_obj.get("customer")
            user_to_cancel = None
            if cust_id:
                for u in subscription_manager._users.values():
                    if getattr(u, "stripe_customer_id", None) == cust_id:
                        user_to_cancel = u
                        break
            if user_to_cancel:
                subscription_manager.cancel_subscription(
                    user_id=user_to_cancel.user_id,
                    reason="Cancelación recibida desde Stripe Subscription"
                )

        return {"success": True, "event_type": event_type, "processed": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# 🔴 Churn Management & Customer Retention Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/v1/cloud/subscription/cancel")
async def cancel_subscription_endpoint(req: CancelSubscriptionRequest):
    """Cancel subscription and record customer churn with departure reason."""
    try:
        return subscription_manager.cancel_subscription(
            user_id=req.user_id,
            reason=req.reason or "Usuario canceló suscripción",
            feedback=req.feedback
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/cloud/subscription/reactivate")
async def reactivate_subscription_endpoint(req: ReactivateSubscriptionRequest):
    """Reactivate a canceled/churned user back to active standing."""
    try:
        return subscription_manager.reactivate_subscription(
            user_id=req.user_id,
            target_tier=req.target_tier
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


__all__ = ["router"]
