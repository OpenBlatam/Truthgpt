"""
🧪 Test Suite for TruthGPT Cloud Monetization, Billing & Executive Churn Dashboard
Validates complete monetization workflows:
- Executive Analytics Dashboard HTML & JSON endpoints
- Tracking of Active Users vs Churned Users vs At-Risk Users
- Stripe Checkout Session creation (Live / Sandbox mode)
- Direct Shareable Payment Link generation
- On-Demand Direct Charging & Invoice Generation
- Customer Churn cancellation & reactivation lifecycle
- Payment Gateway configuration status
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
_current = Path(__file__).resolve().parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from fastapi.testclient import TestClient
from truthgpt_cloud.server import app
from truthgpt_cloud.billing.subscription import subscription_manager

client = TestClient(app)


def test_dashboard_html_view():
    """Verify that the dashboard HTML page is served correctly at /dashboard and /admin."""
    print("Testing GET /dashboard ...")
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "TruthGPT Cloud" in resp.text
    assert "kpiMrr" in resp.text
    assert "paymentModal" in resp.text
    print("  -> /dashboard returns 200 OK with rich HTML view.")

    print("Testing GET /admin ...")
    resp_admin = client.get("/admin")
    assert resp_admin.status_code == 200
    assert "TruthGPT Cloud" in resp_admin.text
    print("  -> /admin returns 200 OK.")


def test_root_content_negotiation():
    """Verify that / redirects browsers to /dashboard but returns JSON for API clients."""
    print("Testing GET / with browser Accept header ...")
    resp_browser = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"}, follow_redirects=False)
    assert resp_browser.status_code in (302, 307)
    assert resp_browser.headers["location"] == "/dashboard"
    print("  -> Browser request correctly redirected to /dashboard.")

    print("Testing GET / with JSON Accept header ...")
    resp_api = client.get("/", headers={"Accept": "application/json"})
    assert resp_api.status_code == 200
    data = resp_api.json()
    assert data["platform"] == "TruthGPT Cloud"
    assert data["dashboard_url"] == "/dashboard"
    print("  -> API request correctly received JSON descriptor with dashboard_url.")


def test_dashboard_overview_api():
    """Verify that /api/v1/cloud/dashboard/overview returns real-time churn & monetization metrics."""
    print("Testing GET /api/v1/cloud/dashboard/overview ...")
    resp = client.get("/api/v1/cloud/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Validate KPIs structure
    kpis = data["kpis"]
    assert "mrr_usd" in kpis
    assert "arr_usd" in kpis
    assert "total_revenue_usd" in kpis
    assert "active_users_count" in kpis
    assert "churned_users_count" in kpis
    assert "dau" in kpis
    assert "churn_rate_pct" in kpis
    assert "retention_rate_pct" in kpis

    # Validate user segments
    assert isinstance(data["active_users"], list)
    assert isinstance(data["churned_users"], list)
    assert isinstance(data["at_risk_users"], list)
    assert isinstance(data["recent_invoices"], list)
    assert isinstance(data["recent_events"], list)
    assert "gateway_status" in data

    print(f"  -> Overview valid! Active: {len(data['active_users'])}, Churned: {len(data['churned_users'])}, MRR: ${kpis['mrr_usd']}")


def test_gateway_status():
    """Verify that payment gateways report operational status."""
    print("Testing GET /api/v1/cloud/gateways/status ...")
    resp = client.get("/api/v1/cloud/gateways/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "stripe" in data["gateways"]
    stripe_info = data["gateways"]["stripe"]
    assert stripe_info["ready_to_charge"] is True
    assert "instructions" in stripe_info
    print(f"  -> Gateway status: Mode={stripe_info['mode']}, Ready={stripe_info['ready_to_charge']}")


def test_checkout_session_creation():
    """Verify that checkout sessions can be generated for subscriptions."""
    print("Testing POST /api/v1/cloud/billing/checkout-session ...")
    payload = {
        "user_id": "usr_default_demo",
        "tier_id": "pro",
        "billing_cycle": "monthly",
        "amount_usd": 19.99
    }
    resp = client.post("/api/v1/cloud/billing/checkout-session", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "checkout_url" in data
    assert "session_id" in data
    print(f"  -> Checkout session created: {data['checkout_url']}")


def test_payment_link_creation():
    """Verify that shareable payment links can be created."""
    print("Testing POST /api/v1/cloud/billing/payment-link ...")
    payload = {
        "user_id": "usr_default_demo",
        "amount_usd": 49.99,
        "description": "TruthGPT Enterprise Token Pack 5M"
    }
    resp = client.post("/api/v1/cloud/billing/payment-link", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "payment_url" in data
    assert "payment_link_id" in data
    assert data["amount_usd"] == 49.99
    print(f"  -> Payment link created: {data['payment_url']}")


def test_direct_charge_and_revenue_update():
    """Verify on-demand direct charging, invoice generation, and revenue accumulation."""
    print("Testing POST /api/v1/cloud/billing/charge-direct ...")
    # Get initial revenue
    overview_before = client.get("/api/v1/cloud/dashboard/overview").json()
    initial_revenue = overview_before["kpis"]["total_revenue_usd"]

    charge_amount = 25.50
    payload = {
        "user_id": "usr_default_demo",
        "amount_usd": charge_amount,
        "description": "Test Verified Compute Usage",
        "payment_method": "stripe_card"
    }
    resp = client.post("/api/v1/cloud/billing/charge-direct", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["amount_usd"] == charge_amount
    assert "invoice" in data
    inv = data["invoice"]
    assert inv["status"] == "paid"
    assert inv["amount_usd"] == charge_amount

    # Verify revenue increased in overview
    overview_after = client.get("/api/v1/cloud/dashboard/overview").json()
    new_revenue = overview_after["kpis"]["total_revenue_usd"]
    assert new_revenue >= initial_revenue + charge_amount - 0.01
    print(f"  -> Direct charge processed! Revenue: ${initial_revenue} -> ${new_revenue}")


def test_churn_and_retention_lifecycle():
    """Verify canceling a subscription (churn) and reactivating it (retention)."""
    print("Testing customer cancellation (churn) ...")
    test_user_id = "usr_churn_test_01"

    # Register a test user
    subscription_manager.register_user(
        email="churn_test@truthgpt.ai",
        name="Test Churn User",
        user_id=test_user_id
    )

    # 1. Cancel user
    cancel_payload = {
        "user_id": test_user_id,
        "reason": "Probando cancelación en suite de pruebas",
        "feedback": "Excelente producto, solo prueba técnica."
    }
    resp_cancel = client.post("/api/v1/cloud/subscription/cancel", json=cancel_payload)
    assert resp_cancel.status_code == 200
    cancel_data = resp_cancel.json()
    assert cancel_data["success"] is True
    assert cancel_data["status"] == "canceled"

    # Check that user shows up in churned_users
    overview = client.get("/api/v1/cloud/dashboard/overview").json()
    churned_ids = [u["user_id"] for u in overview["churned_users"]]
    assert test_user_id in churned_ids
    print(f"  -> User {test_user_id} correctly detected in churned_users list.")

    # 2. Reactivate user
    print("Testing customer reactivation (retention) ...")
    reactivate_payload = {
        "user_id": test_user_id,
        "target_tier": "pro"
    }
    resp_react = client.post("/api/v1/cloud/subscription/reactivate", json=reactivate_payload)
    assert resp_react.status_code == 200
    react_data = resp_react.json()
    assert react_data["success"] is True
    assert react_data["status"] == "active"

    # Check that user is back in active_users
    overview_after = client.get("/api/v1/cloud/dashboard/overview").json()
    active_ids = [u["user_id"] for u in overview_after["active_users"]]
    assert test_user_id in active_ids
    print(f"  -> User {test_user_id} reactivated and returned to active_users list.")


def run_all_tests():
    print("================================================================")
    print("🚀 Running TruthGPT Cloud Monetization & Dashboard Test Suite")
    print("================================================================")
    test_dashboard_html_view()
    test_root_content_negotiation()
    test_dashboard_overview_api()
    test_gateway_status()
    test_checkout_session_creation()
    test_payment_link_creation()
    test_direct_charge_and_revenue_update()
    test_churn_and_retention_lifecycle()
    print("================================================================")
    print("✅ ALL TESTS PASSED! Monetization & Dashboard 100% Operational.")
    print("================================================================")


if __name__ == "__main__":
    run_all_tests()
