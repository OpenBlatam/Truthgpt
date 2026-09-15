"""
🧪 Comprehensive Test Suite for TruthGPT Cloud Monetization, Stripe Billing & Churn Analytics Dashboard
Validates live/sandbox charging, checkout sessions, payment links, user churn tracking, retention KPIs,
and executive HTML/REST dashboard endpoints.
"""

import sys
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root paths
_current = Path(__file__).resolve().parent.parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from truthgpt_cloud import (
    CloudTier,
    SubscriptionManager,
    subscription_manager,
)
from truthgpt_cloud.billing.gateways import PaymentGatewayService
from truthgpt_cloud.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_payment_gateway_status_and_modes():
    """Verify gateway status reporting (Stripe sandbox/live, crypto, wire)."""
    status = PaymentGatewayService.get_gateway_status()
    assert "stripe" in status
    assert "ready_to_charge" in status["stripe"]
    assert status["stripe"]["ready_to_charge"] is True
    assert status["stripe"]["mode"] in ["sandbox_simulated", "test", "live"]
    assert "crypto_usdc" in status
    assert "wire_transfer" in status


def test_create_checkout_session_and_payment_link():
    """Test creating Stripe checkout sessions and shareable payment links."""
    # 1. Checkout session
    cs = PaymentGatewayService.create_checkout_session(
        user_id="usr_default_demo",
        tier_id="pro",
        amount_usd=19.99,
        billing_cycle="monthly"
    )
    assert cs["success"] is True
    assert "session_id" in cs
    assert "checkout_url" in cs
    assert cs["amount_usd"] == 19.99

    # 2. Payment link
    pl = PaymentGatewayService.create_payment_link(
        amount_usd=49.99,
        description="Pack de 1M Tokens TruthGPT Cloud",
        user_id="usr_default_demo"
    )
    assert pl["success"] is True
    assert "payment_url" in pl
    assert pl["amount_usd"] == 49.99
    assert "link_id" in pl["payment_url"]


def test_churn_lifecycle_and_reactivation():
    """Test full customer churn lifecycle: cancellation, reason logging, and reactivation."""
    sm = SubscriptionManager(storage_path=":memory:")
    user = sm.register_user(email="churn_candidate@test.com", name="Candidate Churn", tier=CloudTier.PRO)
    uid = user.user_id

    # 1. Record initial activity
    sm.record_activity(uid, tokens=1500, operation="inference")
    u_active = sm.get_user(uid)
    assert u_active.last_active_at is not None
    assert u_active.total_requests >= 1

    # 2. Cancel subscription (Churn event)
    cancel_res = sm.cancel_subscription(
        user_id=uid,
        reason="Reducción presupuestaria Q3",
        feedback="Excelente producto, regresaremos el próximo año."
    )
    assert cancel_res["success"] is True
    assert cancel_res["churn_status"] == "churned"
    assert cancel_res["status"] == "canceled"
    assert cancel_res["churn_reason"] == "Reducción presupuestaria Q3"

    u_churned = sm.get_user(uid)
    assert u_churned.status == "canceled"
    assert u_churned.churn_status == "churned"
    assert u_churned.churn_date is not None

    # Check dashboard reflects churned user
    dash = sm.get_churn_and_usage_dashboard()
    churned_ids = [u["user_id"] for u in dash["churned_users"]]
    assert uid in churned_ids

    # 3. Reactivate customer
    reactivate_res = sm.reactivate_subscription(user_id=uid, target_tier=CloudTier.ULTRA)
    assert reactivate_res["success"] is True
    assert reactivate_res["status"] == "active"
    assert reactivate_res["tier"] == "ultra"
    assert reactivate_res["churn_status"] == "active"

    # Check dashboard reflects active user again
    dash2 = sm.get_churn_and_usage_dashboard()
    active_ids = [u["user_id"] for u in dash2["active_users"]]
    assert uid in active_ids


def test_dashboard_kpis_calculation():
    """Verify calculated metrics: MRR, ARR, DAU, MAU, Churn Rate and Retention Rate."""
    sm = SubscriptionManager.create_isolated(seed_demo_users=False)
    # Seed 3 users
    u1 = sm.register_user("u1@test.com", "User 1", CloudTier.PRO)
    u2 = sm.register_user("u2@test.com", "User 2", CloudTier.ULTRA)
    u3 = sm.register_user("u3@test.com", "User 3", CloudTier.FREE)

    # Cancel one to simulate churn
    sm.cancel_subscription(u3.user_id, reason="Probó y se fue")

    dash = sm.get_churn_and_usage_dashboard()
    kpis = dash["kpis"]
    assert kpis["total_users"] == 3
    assert kpis["active_users_count"] == 2
    assert kpis["churned_users_count"] == 1
    assert kpis["mrr_usd"] > 0
    assert kpis["arr_usd"] == round(kpis["mrr_usd"] * 12.0, 2)
    assert kpis["churn_rate_pct"] > 0
    assert kpis["retention_rate_pct"] <= 100.0


def test_fastapi_html_dashboard_endpoint(client):
    """Verify GET /dashboard and /admin return the HTML dashboard with 200 OK."""
    resp1 = client.get("/dashboard")
    assert resp1.status_code == 200
    assert "text/html" in resp1.headers["content-type"]
    assert "TruthGPT Cloud" in resp1.text
    assert "Centro de Control" in resp1.text
    assert "Quién lo Usa" in resp1.text
    assert "Quién lo Dejó de Usar" in resp1.text

    resp2 = client.get("/admin")
    assert resp2.status_code == 200
    assert resp2.text == resp1.text


def test_fastapi_dashboard_overview_api(client):
    """Verify GET /api/v1/cloud/dashboard/overview returns structured JSON data."""
    resp = client.get("/api/v1/cloud/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "kpis" in data
    assert "active_users" in data
    assert "churned_users" in data
    assert "at_risk_users" in data
    assert "recent_invoices" in data
    assert "recent_events" in data
    assert "gateway_status" in data


def test_fastapi_billing_checkout_and_charge_endpoints(client):
    """Verify checkout session creation, direct charge, and payment link endpoints."""
    # 1. Checkout session
    resp_cs = client.post("/api/v1/cloud/billing/checkout-session", json={
        "user_id": "usr_default_demo",
        "tier_id": "pro",
        "amount_usd": 19.99,
        "billing_cycle": "monthly"
    })
    assert resp_cs.status_code == 200
    assert resp_cs.json()["success"] is True
    assert "checkout_url" in resp_cs.json()

    # 2. Payment link
    resp_pl = client.post("/api/v1/cloud/billing/payment-link", json={
        "user_id": "usr_default_demo",
        "amount_usd": 25.00,
        "description": "Recarga de Crédito de Inferencia"
    })
    assert resp_pl.status_code == 200
    assert resp_pl.json()["success"] is True
    assert "payment_url" in resp_pl.json()

    # 3. Direct charge
    resp_dc = client.post("/api/v1/cloud/billing/charge-direct", json={
        "user_id": "usr_default_demo",
        "amount_usd": 15.00,
        "description": "Cobro directo de prueba",
        "payment_method": "stripe_card"
    })
    assert resp_dc.status_code == 200
    dc_data = resp_dc.json()
    assert dc_data["success"] is True
    assert dc_data["amount_usd"] == 15.00
    assert "invoice_id" in dc_data


def test_fastapi_cancel_and_reactivate_endpoints(client):
    """Verify POST /api/v1/cloud/subscription/cancel and /reactivate endpoints."""
    # Cancel usr_pro_sample
    resp_cancel = client.post("/api/v1/cloud/subscription/cancel", json={
        "user_id": "usr_pro_sample",
        "reason": "Test de baja de cliente",
        "feedback": "Probando endpoint de churn"
    })
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["churn_status"] == "churned"

    # Reactivate usr_pro_sample
    resp_reactivate = client.post("/api/v1/cloud/subscription/reactivate", json={
        "user_id": "usr_pro_sample",
        "target_tier": "pro"
    })
    assert resp_reactivate.status_code == 200
    assert resp_reactivate.json()["churn_status"] == "active"
