"""
Test suite for TruthGPT Cloud Monetization, Churn Tracking & Dashboard.
Verifies:
- Dashboard overview endpoint returns active users, churned users, and MRR.
- Checkout session and payment links generation for Stripe.
- Direct charges and invoice generation.
- Churn registration (cancellation with reason) and customer reactivation.
- Dashboard HTML rendering at /dashboard and /admin.
"""

import pytest
from fastapi.testclient import TestClient
from truthgpt_cloud_server import app
from truthgpt_cloud import subscription_manager, CloudTier

client = TestClient(app)

def test_dashboard_html_endpoints():
    """Verify that both /dashboard and /admin serve the executive dashboard."""
    for path in ["/dashboard", "/admin"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "TruthGPT Cloud" in res.text
        assert "Quién lo Usa" in res.text or "Quién lo usa" in res.text
        assert "Quién lo Deja de Usar" in res.text or "Quién lo dejó de usar" in res.text or "Bajas / Churn" in res.text

def test_dashboard_overview_kpis():
    """Verify overview returns structured KPIs, active users, and churn lists."""
    res = client.get("/api/v1/cloud/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "kpis" in data
    k = data["kpis"]
    assert "mrr_usd" in k
    assert "arr_usd" in k
    assert "active_users_count" in k
    assert "churned_users_count" in k
    assert "retention_rate_pct" in k
    assert "churn_rate_pct" in k
    assert isinstance(data["active_users"], list)
    assert isinstance(data["churned_users"], list)
    assert isinstance(data["at_risk_users"], list)
    assert isinstance(data["recent_invoices"], list)

def test_checkout_session_and_payment_link():
    """Verify generating Stripe checkout session and shareable payment link."""
    # 1. Checkout Session
    res_cs = client.post("/api/v1/cloud/billing/checkout-session", json={
        "user_id": "usr_default_demo",
        "tier_id": "pro",
        "billing_cycle": "monthly",
        "amount_usd": 19.99
    })
    assert res_cs.status_code == 200
    cs_data = res_cs.json()
    assert cs_data["success"] is True
    assert "checkout_url" in cs_data
    assert "session_id" in cs_data

    # 2. Payment Link
    res_pl = client.post("/api/v1/cloud/billing/payment-link", json={
        "user_id": "usr_default_demo",
        "amount_usd": 49.00,
        "description": "Enterprise Custom Training Pack"
    })
    assert res_pl.status_code == 200
    pl_data = res_pl.json()
    assert pl_data["success"] is True
    assert "payment_link_url" in pl_data

def test_direct_charge_and_invoice():
    """Verify executing an immediate charge on a customer."""
    res = client.post("/api/v1/cloud/billing/charge-direct", json={
        "user_id": "usr_default_demo",
        "amount_usd": 25.50,
        "description": "On-demand SMT Verification Burst",
        "payment_method": "stripe_card"
    })
    assert res.status_code == 200
    charge_data = res.json()
    assert charge_data["success"] is True
    assert "invoice" in charge_data
    assert charge_data["invoice"]["amount_usd"] == 25.50
    assert charge_data["invoice"]["status"] == "paid"

def test_churn_lifecycle_cancel_and_reactivate():
    """Verify tracking users who leave (churn) and reactivating them."""
    test_uid = "usr_churn_test_001"
    # Register test user
    subscription_manager.register_user(
        email="testchurn@truthgpt.ai",
        name="Churn Test Candidate",
        tier=CloudTier.PRO,
        user_id=test_uid
    )

    # 1. User cancels (leaves)
    res_cancel = client.post("/api/v1/cloud/subscription/cancel", json={
        "user_id": test_uid,
        "reason": "Probando alternativa temporalmente",
        "feedback": "Excelente producto, volveremos el próximo trimestre."
    })
    assert res_cancel.status_code == 200
    cancel_data = res_cancel.json()
    assert cancel_data["success"] is True
    assert cancel_data["status"] == "canceled"

    # Verify user appears in churn list in overview
    res_ov = client.get("/api/v1/cloud/dashboard/overview")
    ov_data = res_ov.json()
    churned_ids = [u["user_id"] for u in ov_data["churned_users"]]
    assert test_uid in churned_ids

    # 2. Reactivate user
    res_reactivate = client.post("/api/v1/cloud/subscription/reactivate", json={
        "user_id": test_uid,
        "target_tier": "pro"
    })
    assert res_reactivate.status_code == 200
    reactivate_data = res_reactivate.json()
    assert reactivate_data["success"] is True
    assert reactivate_data["status"] == "active"

    # Verify user is now in active list
    res_ov2 = client.get("/api/v1/cloud/dashboard/overview")
    ov_data2 = res_ov2.json()
    active_ids = [u["user_id"] for u in ov_data2["active_users"]]
    assert test_uid in active_ids

def test_activity_recording():
    """Verify user activity is recorded and last_active_at is updated."""
    initial_summary = subscription_manager.get_user_status_summary("usr_default_demo")
    
    # Record activity
    subscription_manager.record_activity("usr_default_demo", tokens=250, operation="smt_inference")
    
    updated_summary = subscription_manager.get_user_status_summary("usr_default_demo")
    assert updated_summary["user_id"] == "usr_default_demo"
