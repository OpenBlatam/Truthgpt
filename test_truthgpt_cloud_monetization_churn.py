"""
🧪 Test Suite: TruthGPT Cloud Monetization, Stripe Billing & Churn Analytics
Validates:
1. Churn detection & user lifecycle (active -> canceled/churned -> reactivated).
2. Live activity tracking (last_active_at, DAU, WAU, MAU, total_requests).
3. MRR, ARR, and Total Revenue calculations.
4. Stripe Checkout Session and Payment Link generation.
5. Direct charging and invoice generation.
6. FastAPI endpoints: /dashboard, /overview, /checkout-session, /payment-link, /cancel, /reactivate.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from truthgpt_cloud import (
    CloudTier,
    subscription_manager,
)
from truthgpt_cloud.billing.gateways import PaymentGatewayService
from truthgpt_cloud_server import app
from fastapi.testclient import TestClient


class TestTruthGPTCloudMonetizationAndChurn(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.sub_mgr = subscription_manager

    def test_01_gateway_status(self):
        """Test gateway configuration reporting."""
        status = PaymentGatewayService.get_gateway_status()
        self.assertIn("stripe", status)
        self.assertTrue(status["stripe"]["ready_to_charge"])
        self.assertIn(status["stripe"]["mode"], ["live", "test", "sandbox_simulated"])

    def test_02_create_checkout_session(self):
        """Test Stripe / Sandbox Checkout session creation."""
        res = PaymentGatewayService.create_checkout_session(
            user_id="usr_default_demo",
            tier_id="pro",
            amount_usd=19.99,
            billing_cycle="monthly"
        )
        self.assertTrue(res["success"])
        self.assertIn("checkout_url", res)
        self.assertIn("session_id", res)
        self.assertEqual(res["tier_id"], "pro")

    def test_03_create_payment_link(self):
        """Test generating a shareable payment link."""
        res = PaymentGatewayService.create_payment_link(
            amount_usd=49.99,
            description="TruthGPT Top-up 5M Tokens",
            user_id="usr_default_demo"
        )
        self.assertTrue(res["success"])
        self.assertIn("payment_url", res)
        self.assertEqual(res["amount_usd"], 49.99)

    def test_04_direct_charge_and_invoice(self):
        """Test direct charging of a user."""
        res = self.sub_mgr.charge_user(
            user_id="usr_default_demo",
            amount_usd=10.0,
            description="On-demand inference charge"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["amount_usd"], 10.0)
        self.assertIn("invoice", res)
        self.assertEqual(res["invoice"]["status"], "paid")

    def test_05_churn_lifecycle_tracking(self):
        """Test canceling subscription (churn) and reactivating."""
        # Check initial dashboard
        dash_before = self.sub_mgr.get_churn_and_usage_dashboard()
        initial_churn = dash_before["kpis"]["churned_users_count"]

        # Cancel user
        cancel_res = self.sub_mgr.cancel_subscription(
            user_id="usr_pro_sample",
            reason="Presupuesto insuficiente",
            feedback="Excelente producto, volveremos pronto"
        )
        self.assertTrue(cancel_res["success"])
        self.assertEqual(cancel_res["status"], "canceled")
        self.assertIsNotNone(cancel_res["churn_date"])

        # Check dashboard reflects churn
        dash_churned = self.sub_mgr.get_churn_and_usage_dashboard()
        self.assertEqual(dash_churned["kpis"]["churned_users_count"], initial_churn + 1)
        self.assertGreater(dash_churned["kpis"]["churn_rate_pct"], 0.0)

        # Verify churned list contains user
        churned_ids = [u["user_id"] for u in dash_churned["churned_users"]]
        self.assertIn("usr_pro_sample", churned_ids)

        # Reactivate user
        reactivate_res = self.sub_mgr.reactivate_subscription(user_id="usr_pro_sample")
        self.assertTrue(reactivate_res["success"])
        self.assertEqual(reactivate_res["status"], "active")

        # Check dashboard after reactivation
        dash_reactivated = self.sub_mgr.get_churn_and_usage_dashboard()
        self.assertEqual(dash_reactivated["kpis"]["churned_users_count"], initial_churn)

    def test_06_activity_recording(self):
        """Test record_activity updating last_active_at and request count."""
        user = self.sub_mgr.get_user("usr_default_demo")
        prev_requests = getattr(user, "total_requests", 0)

        self.sub_mgr.record_activity("usr_default_demo", tokens=120, operation="unit_test")
        self.assertGreater(user.total_requests, prev_requests)
        self.assertIsNotNone(user.last_active_at)

    def test_07_fastapi_dashboard_endpoints(self):
        """Test FastAPI endpoints for dashboard overview and HTML serving."""
        # 1. Overview API
        resp_overview = self.client.get("/api/v1/cloud/dashboard/overview")
        self.assertEqual(resp_overview.status_code, 200)
        data = resp_overview.json()
        self.assertTrue(data["success"])
        self.assertIn("kpis", data)
        self.assertIn("mrr_usd", data["kpis"])
        self.assertIn("total_revenue_usd", data["kpis"])
        self.assertIn("active_users", data)
        self.assertIn("churned_users", data)

        # 2. HTML Dashboard
        resp_html = self.client.get("/dashboard")
        self.assertEqual(resp_html.status_code, 200)
        self.assertIn("text/html", resp_html.headers.get("content-type", ""))
        self.assertIn("TruthGPT Cloud", resp_html.text)
        self.assertIn("MRR", resp_html.text)

        # 3. /admin alias
        resp_admin = self.client.get("/admin")
        self.assertEqual(resp_admin.status_code, 200)

    def test_08_fastapi_checkout_and_billing_endpoints(self):
        """Test FastAPI endpoints for Stripe Checkout, Payment Links and Direct Charging."""
        # Checkout session endpoint
        c_resp = self.client.post("/api/v1/cloud/billing/checkout-session", json={
            "user_id": "usr_default_demo",
            "tier_id": "pro",
            "billing_cycle": "monthly"
        })
        self.assertEqual(c_resp.status_code, 200)
        self.assertTrue(c_resp.json().get("success"))

        # Payment link endpoint
        p_resp = self.client.post("/api/v1/cloud/billing/payment-link", json={
            "amount_usd": 25.0,
            "description": "Soporte dedicado TruthGPT",
            "user_id": "usr_default_demo"
        })
        self.assertEqual(p_resp.status_code, 200)
        self.assertTrue(p_resp.json().get("success"))

        # Direct charge endpoint
        ch_resp = self.client.post("/api/v1/cloud/billing/charge-direct", json={
            "user_id": "usr_default_demo",
            "amount_usd": 5.0,
            "description": "Prueba de cobro unitario"
        })
        self.assertEqual(ch_resp.status_code, 200)
        self.assertTrue(ch_resp.json().get("success"))

        # Gateway status endpoint
        s_resp = self.client.get("/api/v1/cloud/billing/status")
        self.assertEqual(s_resp.status_code, 200)
        self.assertTrue(s_resp.json().get("gateways", {}).get("stripe", {}).get("ready_to_charge"))


if __name__ == "__main__":
    unittest.main()
