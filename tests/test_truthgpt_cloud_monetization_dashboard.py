"""
🧪 TruthGPT Cloud - Monetization & Executive Churn Dashboard Test Suite
Validates web dashboard endpoints, KPIs, Stripe checkout session generation,
direct charging, churn lifecycle management (cancellation & reactivation),
and Stripe webhook event handlers.
"""

import pytest
from fastapi.testclient import TestClient

from truthgpt_cloud.server import app
from truthgpt_cloud import subscription_manager, TruthGPTCloudClient, CloudTier
from truthgpt_cloud.billing.gateways import PaymentGatewayService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_dashboard_html_serves(client):
    """Test that GET /dashboard, /admin and /api/v1/cloud/dashboard serve the full HTML interface."""
    for path in ["/dashboard", "/admin", "/api/v1/cloud/dashboard"]:
        resp = client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "TruthGPT Cloud" in resp.text
        assert "Centro de Control, Cobros y Analítica de Churn" in resp.text
        assert "kpiMrr" in resp.text
        assert "fetchDashboardData" in resp.text


def test_root_redirects_to_dashboard(client):
    """Test that root URL (/) redirects to /dashboard."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/dashboard"


def test_dashboard_overview_kpis(client):
    """Test GET /api/v1/cloud/dashboard/overview returns all business KPIs and user segments."""
    resp = client.get("/api/v1/cloud/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    kpis = data["kpis"]
    assert "mrr_usd" in kpis
    assert "arr_usd" in kpis
    assert "total_revenue_usd" in kpis
    assert "dau" in kpis
    assert "wau" in kpis
    assert "mau" in kpis
    assert "churn_rate_pct" in kpis
    assert "retention_rate_pct" in kpis
    assert "active_users_count" in kpis
    assert "churned_users_count" in kpis
    assert "at_risk_users_count" in kpis

    # Verify lists
    assert isinstance(data["active_users"], list)
    assert isinstance(data["churned_users"], list)
    assert isinstance(data["at_risk_users"], list)
    assert isinstance(data["recent_invoices"], list)
    assert "gateway_status" in data


def test_gateway_status_endpoint(client):
    """Test GET /api/v1/cloud/billing/status."""
    resp = client.get("/api/v1/cloud/billing/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "stripe" in data["gateways"]
    assert data["gateways"]["stripe"]["ready_to_charge"] is True


def test_create_checkout_session(client):
    """Test POST /api/v1/cloud/billing/checkout-session generates valid checkout URL."""
    payload = {
        "user_id": "usr_default_demo",
        "tier_id": "ultra",
        "amount_usd": 99.0,
        "billing_cycle": "monthly",
        "customer_email": "demo@truthgpt.ai"
    }
    resp = client.post("/api/v1/cloud/billing/checkout-session", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "session_id" in data
    assert "checkout_url" in data
    assert data["status"] == "ready"


def test_create_payment_link(client):
    """Test POST /api/v1/cloud/billing/payment-link generates instant link."""
    payload = {
        "amount_usd": 49.99,
        "description": "TruthGPT Cloud 5M Extra Tokens Pack",
        "user_id": "usr_default_demo"
    }
    resp = client.post("/api/v1/cloud/billing/payment-link", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "payment_url" in data
    assert data["amount_usd"] == 49.99


def test_charge_direct_executes_payment(client):
    """Test POST /api/v1/cloud/billing/charge-direct executes on-demand charge and registers invoice."""
    payload = {
        "user_id": "usr_default_demo",
        "amount_usd": 15.00,
        "description": "TruthGPT Cloud SMT Proof Acceleration Run",
        "payment_method": "stripe_card"
    }
    resp = client.post("/api/v1/cloud/billing/charge-direct", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["amount_usd"] == 15.00
    assert "invoice" in data
    assert data["invoice"]["status"] == "paid"

    # Verify invoice appears in user's profile
    user = subscription_manager.get_user("usr_default_demo")
    assert any(inv.invoice_id == data["invoice"]["invoice_id"] for inv in user.invoices)


def test_customer_portal_session(client):
    """Test POST /api/v1/cloud/billing/portal-session."""
    payload = {"user_id": "usr_default_demo"}
    resp = client.post("/api/v1/cloud/billing/portal-session", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "portal_url" in data


def test_churn_lifecycle_cancel_and_reactivate(client):
    """Test cancelling user subscription (churn) and subsequent reactivation."""
    test_user_id = "usr_test_lifecycle_user"

    # Register temporary test user
    sub = subscription_manager.register_user(
        email="lifecycle@test.io",
        name="Lifecycle Corp",
        tier=CloudTier.PRO,
        user_id=test_user_id
    )
    assert sub.status == "active"

    # 1. Cancel / Churn user
    cancel_payload = {
        "user_id": test_user_id,
        "reason": "Probando cancelación en suite automatizada",
        "feedback": "Volveremos pronto"
    }
    resp_cancel = client.post("/api/v1/cloud/subscription/cancel", json=cancel_payload)
    assert resp_cancel.status_code == 200
    data_cancel = resp_cancel.json()
    assert data_cancel["success"] is True
    assert data_cancel["status"] == "canceled"

    # Verify dashboard reflects churn
    overview_resp = client.get("/api/v1/cloud/dashboard/overview")
    overview = overview_resp.json()
    churned_ids = [u["user_id"] for u in overview["churned_users"]]
    assert test_user_id in churned_ids

    # 2. Reactivate user
    reactivate_payload = {
        "user_id": test_user_id,
        "target_tier": "pro"
    }
    resp_react = client.post("/api/v1/cloud/subscription/reactivate", json=reactivate_payload)
    assert resp_react.status_code == 200
    data_react = resp_react.json()
    assert data_react["success"] is True
    assert data_react["status"] == "active"

    # Verify dashboard reflects reactivation
    overview_resp2 = client.get("/api/v1/cloud/dashboard/overview")
    overview2 = overview_resp2.json()
    active_ids = [u["user_id"] for u in overview2["active_users"]]
    assert test_user_id in active_ids


def test_stripe_webhook_handling(client):
    """Test Stripe webhook receiver for checkout.session.completed and subscription canceled."""
    # 1. Checkout completed webhook
    checkout_event = {
        "id": "evt_test_checkout_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "usr_default_demo",
                "customer": "cus_stripe_live_demo_001",
                "metadata": {
                    "user_id": "usr_default_demo",
                    "tier_id": "ultra",
                    "billing_cycle": "yearly"
                }
            }
        }
    }
    resp = client.post("/api/v1/cloud/billing/webhook/stripe", json=checkout_event)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["event_type"] == "checkout.session.completed"

    # 2. Unknown event graceful handling
    dummy_event = {"id": "evt_test_dummy", "type": "payment_intent.created", "data": {}}
    resp2 = client.post("/api/v1/cloud/billing/webhook/stripe", json=dummy_event)
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True


def test_client_sdk_monetization_methods():
    """Test TruthGPTCloudClient SDK monetization and dashboard helpers."""
    client_sdk = TruthGPTCloudClient(user_id="usr_default_demo")

    dash = client_sdk.get_churn_and_usage_dashboard()
    assert dash["success"] is True
    assert "kpis" in dash
    assert dash["kpis"]["mrr_usd"] > 0

    gateways = client_sdk.get_payment_gateways_status()
    assert gateways["stripe"]["ready_to_charge"] is True

    # Test direct charge via client
    charge_res = client_sdk.charge_user(amount_usd=5.0, description="Client SDK Test Charge")
    assert charge_res["success"] is True
    assert charge_res["amount_usd"] == 5.0
