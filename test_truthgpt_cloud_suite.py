"""
🧪 TruthGPT Cloud - Comprehensive Test & Validation Suite
Validates:
1. Subscription tiers definition & feature matrix
2. User registration, scoped keys, and persistence
3. Tier upgrade & invoice generation
4. Token Bucket rate limiting & quota enforcement
5. Z3 SMT Theorem Prover, AST parser & Merkle Proof Trees
6. Hoare-logic Design-by-Contract (DbC) verification
7. Multi-Agent Cloud Swarm execution & consensus scoring
8. Cloud Intelligence Router & streaming inference
9. FastAPI Server REST & SSE Endpoints
"""

import sys
import os
import uuid
import asyncio
import unittest
from pathlib import Path

# Ensure paths
_current = Path(__file__).resolve().parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from truthgpt_cloud import (
    CloudTier,
    get_tier_config,
    get_all_tiers,
    subscription_manager,
    cloud_verifier,
    cloud_swarm,
    cloud_router,
    TruthGPTCloudClient,
    TokenBucketRateLimiter,
    RateLimitExceeded
)


class TestTruthGPTCloud(unittest.TestCase):

    def setUp(self):
        self.sub_mgr = subscription_manager
        self.verifier = cloud_verifier
        self.swarm = cloud_swarm
        self.router = cloud_router
        self.client = TruthGPTCloudClient()

    def test_01_tiers_catalog(self):
        """Verify that all tiers exist and conform to specifications."""
        tiers = get_all_tiers()
        self.assertEqual(len(tiers), 4, "Debe haber exactamente 4 tiers definidos (Free, Pro, Ultra, Enterprise).")
        
        tier_ids = [t["tier_id"] for t in tiers]
        self.assertIn("free", tier_ids)
        self.assertIn("pro", tier_ids)
        self.assertIn("ultra", tier_ids)
        self.assertIn("enterprise", tier_ids)
        
        # Verify Pro tier specifications
        pro_cfg = get_tier_config(CloudTier.PRO)
        self.assertEqual(pro_cfg.price_monthly_usd, 19.99)
        self.assertEqual(pro_cfg.context_window_tokens, 200_000)
        self.assertEqual(pro_cfg.smt_z3_verification_depth, 2)
        self.assertTrue(pro_cfg.proof_certificate_generation)

    def test_02_user_registration_and_key_generation(self):
        """Test registering a new user, checking tier limits, and managing scoped API keys."""
        test_email = f"tester_{uuid.uuid4().hex[:6]}@truthgpt.ai"
        user = self.sub_mgr.register_user(
            email=test_email,
            name="Cloud Tester",
            tier=CloudTier.FREE
        )
        self.assertIsNotNone(user.user_id)
        self.assertEqual(user.email, test_email)
        self.assertEqual(user.tier, CloudTier.FREE)
        self.assertEqual(len(user.api_keys), 1)
        self.assertTrue(user.api_keys[0].startswith("tgpt_cloud_live_"))
        
        # Free tier has a 1-key limit; generating a second key must raise ValueError
        with self.assertRaises(ValueError):
            self.sub_mgr.generate_new_api_key(user.user_id)
            
        # Upgrade to Pro to test generating additional API keys (Pro allows up to 5)
        self.sub_mgr.upgrade_subscription(user.user_id, CloudTier.PRO)
        new_key = self.sub_mgr.generate_new_api_key(user.user_id, label="Worker Key", scopes=["inference", "verify"])
        self.assertTrue(new_key.startswith("tgpt_cloud_live_"))
        updated_user = self.sub_mgr.get_user(user.user_id)
        self.assertEqual(len(updated_user.api_keys), 2)

    def test_03_subscription_upgrade_and_invoicing(self):
        """Test upgrading from Free to Pro and generating compliant invoice."""
        test_email = f"upgrade_{uuid.uuid4().hex[:6]}@truthgpt.ai"
        user = self.sub_mgr.register_user(email=test_email, name="Upgrader", tier=CloudTier.FREE)
        
        # Upgrade to Pro (Monthly)
        result = self.sub_mgr.upgrade_subscription(
            user_id=user.user_id,
            target_tier=CloudTier.PRO,
            billing_cycle="monthly",
            payment_method="stripe_card"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["tier"], "pro")
        self.assertEqual(result["invoice"]["amount_usd"], 19.99)
        self.assertEqual(result["invoice"]["status"], "paid")
        
        # Check that user metrics updated
        user_summary = self.sub_mgr.get_user_status_summary(user.user_id)
        self.assertEqual(user_summary["tier"], "pro")
        self.assertEqual(user_summary["metrics"]["daily_token_limit"], 2_000_000)
        self.assertEqual(len(user_summary["invoices"]), 1)

    def test_04_token_bucket_rate_limiter(self):
        """Test Token Bucket RPM rate limiter enforcing limits."""
        limiter = TokenBucketRateLimiter()
        uid = f"test_user_rate_{uuid.uuid4().hex[:6]}"
        
        # Free tier capacity = 15 RPM
        # Consume 15 tokens successfully
        for _ in range(15):
            self.assertTrue(limiter.check_and_consume(uid, rpm_capacity=15, cost=1.0))
            
        # 16th request must raise RateLimitExceeded
        with self.assertRaises(RateLimitExceeded):
            limiter.check_and_consume(uid, rpm_capacity=15, cost=1.0)

    def test_05_z3_formal_verifier_and_merkle_tree(self):
        """Test Z3 SMT Theorem Prover with AST parsing and Merkle proof tree generation."""
        claim = "∀x, y ∈ ℝ: (x + y)^2 >= 4xy"
        cert = self.verifier.verify_claim(
            claim=claim,
            constraints=["x > 0", "y > 0"],
            depth_level=2
        )
        self.assertIsNotNone(cert.certificate_id)
        self.assertIn(cert.status, ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"])
        self.assertTrue(len(cert.solver_engine) > 0)
        self.assertGreater(cert.confidence_score, 0.90)
        self.assertTrue(cert.proof_tree_hash.startswith("0x"))
        self.assertTrue(len(cert.mathematical_invariants) >= 1)
        self.assertGreater(len(cert.proof_steps), 0)

    def test_06_hoare_contract_verification(self):
        """Test Design-by-Contract (Hoare Logic) contract verification."""
        res = self.verifier.verify_contract(
            preconditions=["x >= 0", "y >= 0"],
            postconditions=["x + y >= 0"],
            invariants=["x in Real", "y in Real"],
            function_name="fast_loss_optimizer"
        )
        self.assertEqual(res.overall_status, "VERIFIED")
        self.assertTrue(res.preconditions_verified)
        self.assertTrue(res.postconditions_verified)
        self.assertTrue(res.invariants_preserved)
        self.assertTrue(res.certificate.proof_tree_hash.startswith("0x"))

    def test_07_multi_agent_cloud_swarm(self):
        """Test asynchronous multi-agent swarm orchestration and quantitative consensus."""
        async def run_swarm_test():
            trace = await self.swarm.execute_swarm_session(
                prompt="Demostrar la convergencia de la serie armónica alternada",
                user_id="usr_default_demo",
                max_agents=5,
                depth_level=2
            )
            self.assertIsNotNone(trace.session_id)
            self.assertGreaterEqual(len(trace.agents_involved), 4)
            self.assertTrue(len(trace.consensus_summary) > 10)
            self.assertGreater(trace.consensus_score, 0.95)
            self.assertGreater(trace.execution_time_ms, 0)
            
        asyncio.run(run_swarm_test())

    def test_08_cloud_intelligence_router_and_streaming(self):
        """Test end-to-end cloud inference routing and SSE streaming generator."""
        async def run_router_test():
            # 1. Direct route inference
            response = await self.router.route_inference(
                prompt="Optimizar y verificar invariante para algoritmo de ordenamiento cuasi-lineal",
                user_id="usr_default_demo",
                enable_swarm=False,
                enable_formal_verification=True
            )
            self.assertIsNotNone(response.response_id)
            self.assertTrue(response.verification_passed)
            self.assertGreater(response.confidence_score, 0.85)
            self.assertGreater(response.tokens_consumed, 0)
            
            # 2. Streaming inference
            chunks = []
            async for chunk in self.router.stream_inference(
                prompt="Verificar convergencia asintótica",
                user_id="usr_default_demo"
            ):
                chunks.append(chunk)
            self.assertGreater(len(chunks), 1)
            
        asyncio.run(run_router_test())

    def test_09_fastapi_endpoints_complete(self):
        """Test FastAPI Server HTTP and Contract verification endpoints."""
        from fastapi.testclient import TestClient
        from truthgpt_cloud_server import app
        
        client = TestClient(app)
        
        # Test GET /api/v1/cloud/tiers
        resp_tiers = client.get("/api/v1/cloud/tiers")
        self.assertEqual(resp_tiers.status_code, 200)
        data_tiers = resp_tiers.json()
        self.assertTrue(data_tiers["success"])
        self.assertEqual(len(data_tiers["tiers"]), 4)

        # Test GET /api/v1/cloud/models
        resp_models = client.get("/api/v1/cloud/models")
        self.assertEqual(resp_models.status_code, 200)
        self.assertGreaterEqual(len(resp_models.json()["models"]), 3)
        
        # Test POST /api/v1/cloud/auth/signup
        test_email = f"api_user_{uuid.uuid4().hex[:6]}@truthgpt.ai"
        resp_signup = client.post("/api/v1/cloud/auth/signup", json={
            "email": test_email,
            "name": "API Tester",
            "initial_tier": "free"
        })
        self.assertEqual(resp_signup.status_code, 200)
        signup_data = resp_signup.json()
        self.assertTrue(signup_data["success"])
        user_id = signup_data["user_id"]
        
        # Test GET /api/v1/cloud/subscription/me
        resp_me = client.get(f"/api/v1/cloud/subscription/me?user_id={user_id}")
        self.assertEqual(resp_me.status_code, 200)
        me_data = resp_me.json()
        self.assertEqual(me_data["subscription"]["tier"], "free")
        
        # Test POST /api/v1/cloud/subscription/upgrade
        resp_upgrade = client.post("/api/v1/cloud/subscription/upgrade", json={
            "user_id": user_id,
            "target_tier": "ultra",
            "billing_cycle": "yearly",
            "payment_method": "crypto_usdc"
        })
        self.assertEqual(resp_upgrade.status_code, 200)
        upgrade_data = resp_upgrade.json()
        self.assertTrue(upgrade_data["success"])
        self.assertEqual(upgrade_data["new_tier"], "ultra")
        
        # Test POST /api/v1/cloud/formal/verify
        resp_verify = client.post("/api/v1/cloud/formal/verify", json={
            "claim": "∀a, b ∈ ℝ: a^2 - b^2 = (a-b)(a+b)",
            "tier_depth": 2
        })
        self.assertEqual(resp_verify.status_code, 200)
        verify_data = resp_verify.json()
        self.assertTrue(verify_data["success"])
        self.assertIn("certificate", verify_data)

        # Test POST /api/v1/cloud/formal/verify/contract
        resp_contract = client.post("/api/v1/cloud/formal/verify/contract", json={
            "function_name": "cuda_attention_kernel",
            "preconditions": ["seq_len > 0", "head_dim == 64"],
            "postconditions": ["output_norm >= 0"],
            "invariants": ["memory_offset < 1024"]
        })
        self.assertEqual(resp_contract.status_code, 200)
        self.assertTrue(resp_contract.json()["success"])
        
        # Test GET /api/v1/cloud/papers/hub
        resp_papers = client.get("/api/v1/cloud/papers/hub")
        self.assertEqual(resp_papers.status_code, 200)
        self.assertGreater(len(resp_papers.json()), 0)


if __name__ == "__main__":
    unittest.main()
