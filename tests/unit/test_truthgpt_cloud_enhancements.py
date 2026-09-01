"""
🛡️ TruthGPT Cloud - Comprehensive Enhancements Test Suite
Validates advanced formal verification, HMAC certificate signing, SMT-LIB2 exporting,
differential privacy, attention invariants, webhook signature verification,
usage analytics, async context manager in client SDK, and server endpoints.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from truthgpt_cloud import (
    CloudTier,
    cloud_verifier,
    cloud_swarm,
    subscription_manager,
    webhook_manager,
    proof_cache,
    TruthGPTCloudClient,
)
from truthgpt_cloud_server import app


class TestTruthGPTCloudEnhancements:
    """Test suite for new capabilities and improvements added to TruthGPT Cloud."""

    def test_01_proof_certificate_custom_hmac_signing_and_verification(self):
        """Verify custom secret HMAC-SHA256 signature and integrity verification."""
        cert = cloud_verifier.verify_expression("x^2 + y^2 >= 0", constraints=["x >= 0", "y >= 0"], tier_depth=2)
        assert cert.signature_hmac is not None
        assert cert.verify_integrity() is True

        custom_key = b"enterprise-custom-sovereign-key-9988"
        custom_sig = cert.sign_certificate(custom_key)
        assert custom_sig != ""
        assert cert.verify_hmac_signature(custom_key) is True
        assert cert.verify_hmac_signature(b"wrong-key") is False

    def test_02_smt2_export(self):
        """Verify SMT-LIB 2.0 script generation from verified proof certificate."""
        cert = cloud_verifier.verify_expression("(x + y)^2 == x^2 + 2*x*y + y^2", tier_depth=2)
        smt2_script = cloud_verifier.export_to_smt2(cert)
        assert ";; TruthGPT Cloud - Formal SMT-LIB2 Proof Script" in smt2_script
        assert "(set-logic QF_NRA)" in smt2_script
        assert "(check-sat)" in smt2_script

    def test_03_attention_invariants_verification(self):
        """Verify Transformer Multi-Head & Grouped-Query Attention invariants."""
        res_mha = cloud_verifier.verify_attention_invariants(
            query_shape=[2, 512, 32, 128],
            key_shape=[2, 512, 32, 128],
            value_shape=[2, 512, 32, 128],
            num_heads_q=32,
            num_heads_kv=32,
            head_dim=128,
            is_causal=True
        )
        assert res_mha["success"] is True
        assert res_mha["is_valid"] is True
        assert res_mha["scale_factor"] > 0
        assert res_mha["merkle_root"].startswith("0x")
        assert len(res_mha["invariants_verified"]) >= 4

        # Test GQA mismatch (32 heads not divisible by 5)
        res_gqa_invalid = cloud_verifier.verify_attention_invariants(
            query_shape=[2, 512, 32, 128],
            key_shape=[2, 512, 5, 128],
            value_shape=[2, 512, 5, 128],
            num_heads_q=32,
            num_heads_kv=5,
            head_dim=128
        )
        assert res_gqa_invalid["is_valid"] is False

    def test_04_differential_privacy_verification(self):
        """Verify (eps, delta)-Differential Privacy bounds and Lipschitz continuity."""
        res_dp = cloud_verifier.verify_differential_privacy(
            epsilon=0.5,
            delta=1e-5,
            clipping_bound=1.0,
            noise_multiplier=1.2
        )
        assert res_dp["success"] is True
        assert res_dp["is_valid"] is True
        assert res_dp["required_noise_multiplier"] > 0
        assert res_dp["merkle_root"].startswith("0x")
        assert res_dp["proof_certificate"]["status"] == "DP_GUARANTEE_VERIFIED"

    def test_05_webhook_signature_generation_and_verification(self):
        """Verify Webhook HMAC-SHA256 signature dispatching and verification."""
        secret = "test_custom_webhook_secret_123"
        evt = webhook_manager.emit_event(
            event_type="subscription.renewed",
            user_id="usr_default_demo",
            data={"amount_usd": 19.99, "plan": "pro"},
            custom_secret=secret
        )
        assert evt.signature.startswith("sha256=")

        payload_dict = {
            "event_id": evt.event_id,
            "event_type": evt.event_type,
            "user_id": evt.user_id,
            "timestamp": evt.timestamp,
            "data": evt.data
        }
        is_valid = webhook_manager.verify_webhook_signature(payload_dict, evt.signature, secret=secret)
        assert is_valid is True

        is_invalid = webhook_manager.verify_webhook_signature(payload_dict, evt.signature, secret="wrong_secret")
        assert is_invalid is False

    def test_06_usage_analytics_generation(self):
        """Verify comprehensive token, operation, and cost analytics generation."""
        analytics = subscription_manager.get_usage_analytics("usr_default_demo")
        assert analytics["user_id"] == "usr_default_demo"
        assert "tokens" in analytics
        assert "operations" in analytics
        assert "efficiency" in analytics
        assert analytics["tokens"]["daily_limit"] > 0

    @pytest.mark.asyncio
    async def test_07_client_sdk_async_context_manager_and_methods(self):
        """Verify TruthGPTCloudClient async context manager and new helper methods."""
        async with TruthGPTCloudClient(user_id="usr_default_demo") as client:
            assert client.user_id == "usr_default_demo"
            assert client.tier in [CloudTier.FREE, CloudTier.PRO, CloudTier.ULTRA, CloudTier.ENTERPRISE]

            # Test ask
            res = await client.ask_async("Demostrar consistencia de norma L2 ||x|| >= 0")
            assert res.execution_time_ms > 0
            assert res.verification_passed is True

            # Test verify_attention
            attn_res = client.verify_attention(
                query_shape=[1, 128, 16, 64],
                key_shape=[1, 128, 16, 64],
                value_shape=[1, 128, 16, 64],
                num_heads_q=16,
                head_dim=64
            )
            assert attn_res["is_valid"] is True

            # Test verify_differential_privacy
            dp_res = client.verify_differential_privacy(epsilon=1.0, delta=1e-5)
            assert dp_res["is_valid"] is True

            # Test get_usage_analytics
            analytics = client.get_usage_analytics()
            assert analytics["user_id"] == "usr_default_demo"

    def test_08_client_sdk_sync_context_manager(self):
        """Verify TruthGPTCloudClient synchronous context manager."""
        with TruthGPTCloudClient(user_id="usr_default_demo") as client:
            assert client.user_id == "usr_default_demo"
            status = client.get_subscription_status()
            assert status["tier"] is not None

    def test_09_fastapi_server_new_endpoints(self):
        """Verify new FastAPI REST API endpoints for attention, DP, SMT2 export, and analytics."""
        client = TestClient(app)

        # 1. Differential Privacy endpoint
        dp_resp = client.post(
            "/api/v1/cloud/formal/verify/differential-privacy",
            json={"epsilon": 1.0, "delta": 1e-5, "clipping_bound": 1.0, "noise_multiplier": 1.1}
        )
        assert dp_resp.status_code == 200
        dp_json = dp_resp.json()
        assert dp_json["is_valid"] is True
        assert dp_json["merkle_root"].startswith("0x")

        # 2. SMT2 Export endpoint
        smt2_resp = client.post(
            "/api/v1/cloud/formal/verify/export/smt2",
            json={"claim": "x >= 0 -> x + 1 > 0", "constraints": ["x >= 0"]}
        )
        assert smt2_resp.status_code == 200
        smt2_json = smt2_resp.json()
        assert smt2_json["success"] is True
        assert "(set-logic QF_NRA)" in smt2_json["smt2_script"]

        # 3. Usage Analytics endpoint
        analytics_resp = client.get(
            "/api/v1/cloud/usage/analytics?user_id=usr_default_demo",
            headers={"X-API-Key": "tgpt_cloud_live_demo"}
        )
        assert analytics_resp.status_code == 200
        assert analytics_resp.json()["success"] is True
        assert "tokens" in analytics_resp.json()["analytics"]

        # 4. Webhook Verify endpoint
        test_payload = {"event_id": "evt_test", "event_type": "test", "user_id": "usr_test", "timestamp": 123.0, "data": {}}
        import hmac, hashlib, json
        canonical = json.dumps(test_payload, sort_keys=True)
        sig = hmac.new(b"tgpt_global_webhook_secret", canonical.encode(), hashlib.sha256).hexdigest()
        
        wh_verify_resp = client.post(
            "/api/v1/cloud/webhooks/verify",
            json={"payload": test_payload, "signature": f"sha256={sig}"}
        )
        assert wh_verify_resp.status_code == 200
        assert wh_verify_resp.json()["is_valid"] is True
