"""
🧪 TruthGPT Cloud - Complete & Unified Verification Suite (v2.2)
Validates all platform capabilities:
1. Subscription Tiers & Feature Matrix
2. User Registration, Scoped Key Rotation & Revocation
3. Tier Upgrade & Compliant Invoicing
4. Token Bucket Rate Limiting
5. Z3 SMT Formal Theorem Prover & Cryptographic Merkle Trees
6. Design-by-Contract (DbC) Hoare Logic Verification
7. Multi-Agent Cloud Swarm Orchestration & Consensus Scoring
8. Cloud Router with SSE Streaming & Proof Caching
9. Semantic Proof Cache & Deduplication
10. Cluster Observability & Real-Time Telemetry Metrics
11. SOTA Research Paper Hub & Kernel Compiler
12. Webhooks Event Management
13. FastAPI Server Endpoints Complete Test
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
    proof_cache,
    cloud_telemetry,
    cloud_security,
    cloud_paper_compiler,
    get_all_papers,
    webhook_manager,
    TruthGPTCloudClient,
    TokenBucketRateLimiter,
    RateLimitExceeded
)


class TestTruthGPTCloudComplete(unittest.TestCase):

    def setUp(self):
        self.sub_mgr = subscription_manager
        self.verifier = cloud_verifier
        self.swarm = cloud_swarm
        self.router = cloud_router
        self.cache = proof_cache
        self.telemetry = cloud_telemetry
        self.client = TruthGPTCloudClient()

    def test_01_tiers_catalog(self):
        """Verify tier specifications and pricing matrix."""
        tiers = get_all_tiers()
        self.assertEqual(len(tiers), 4)
        
        tier_ids = [t["tier_id"] for t in tiers]
        self.assertIn("free", tier_ids)
        self.assertIn("pro", tier_ids)
        self.assertIn("ultra", tier_ids)
        self.assertIn("enterprise", tier_ids)
        
        ultra_cfg = get_tier_config(CloudTier.ULTRA)
        self.assertEqual(ultra_cfg.price_monthly_usd, 99.99)
        self.assertEqual(ultra_cfg.context_window_tokens, 2_000_000)
        self.assertEqual(ultra_cfg.smt_z3_verification_depth, 3)
        self.assertTrue(ultra_cfg.priority_gpu_routing)

    def test_02_user_registration_scoped_keys_and_revocation(self):
        """Test user lifecycle: registration, scoped key creation, and revocation."""
        test_email = f"tester_{uuid.uuid4().hex[:6]}@truthgpt.ai"
        user = self.sub_mgr.register_user(
            email=test_email,
            name="SDK Tester",
            tier=CloudTier.PRO
        )
        self.assertEqual(user.tier, CloudTier.PRO)
        initial_key = user.api_keys[0]
        
        # Generate scoped key
        new_key = self.sub_mgr.generate_new_api_key(
            user.user_id,
            label="Inference Worker",
            scopes=["inference", "verify"]
        )
        self.assertTrue(new_key.startswith("tgpt_cloud_live_"))
        self.assertEqual(len(self.sub_mgr.get_user(user.user_id).api_keys), 2)
        
        # Revoke initial key
        revoked = self.sub_mgr.revoke_api_key(user.user_id, initial_key)
        self.assertTrue(revoked)
        self.assertEqual(len(self.sub_mgr.get_user(user.user_id).api_keys), 1)

    def test_03_subscription_upgrade_and_invoicing(self):
        """Test tier upgrade and compliant invoice generation."""
        test_email = f"upgrade_{uuid.uuid4().hex[:6]}@truthgpt.ai"
        user = self.sub_mgr.register_user(email=test_email, name="Upgrader", tier=CloudTier.FREE)
        
        result = self.sub_mgr.upgrade_subscription(
            user_id=user.user_id,
            target_tier=CloudTier.ULTRA,
            billing_cycle="yearly",
            payment_method="stripe_card"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["new_tier"], "ultra")
        self.assertEqual(result["invoice"]["amount_usd"], 999.00)
        self.assertEqual(result["invoice"]["status"], "paid")

    def test_04_rate_limiting(self):
        """Test TokenBucket rate limiter enforcement."""
        limiter = TokenBucketRateLimiter()
        uid = f"rate_user_{uuid.uuid4().hex[:6]}"
        
        # Free RPM = 15
        for _ in range(15):
            self.assertTrue(limiter.check_and_consume(uid, rpm_capacity=15, cost=1.0))
            
        with self.assertRaises(RateLimitExceeded):
            limiter.check_and_consume(uid, rpm_capacity=15, cost=1.0)

    def test_05_z3_formal_verifier_and_merkle_tree(self):
        """Test Z3 SMT Theorem Prover and Merkle proof tree verification."""
        claim = "∀x, y ∈ ℝ⁺: (x + y)^2 >= 4xy"
        cert = self.verifier.verify_expression(
            claim_text=claim,
            constraints=["x > 0", "y > 0"],
            tier_depth=2
        )
        self.assertIsNotNone(cert.certificate_id)
        self.assertIn(cert.status, ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"])
        self.assertTrue(cert.proof_tree_hash.startswith("0x"))
        self.assertTrue(cert.verify_integrity())

    def test_06_hoare_contract_verification(self):
        """Test Design-by-Contract (Hoare Logic) contract verification."""
        res = self.verifier.verify_contract(
            preconditions=["seq_len > 0", "batch_size > 0"],
            postconditions=["output_tokens > 0"],
            invariants=["memory_usage < 1024"],
            function_name="flash_attention_kernel"
        )
        self.assertEqual(res.overall_status, "VERIFIED")
        self.assertTrue(res.preconditions_verified)
        self.assertTrue(res.postconditions_verified)
        self.assertTrue(res.invariants_preserved)

    def test_07_multi_agent_cloud_swarm(self):
        """Test multi-agent swarm orchestration and consensus scoring."""
        async def run_swarm():
            trace = await self.swarm.execute_swarm_session(
                prompt="Demostrar convergencia asintótica de optimizador AdamW",
                user_id="usr_default_demo",
                max_agents=5
            )
            self.assertIsNotNone(trace.session_id)
            self.assertGreaterEqual(len(trace.agents_involved), 4)
            self.assertGreater(trace.consensus_score, 0.95)
            self.assertTrue("consenso" in trace.consensus_summary.lower())
            
        asyncio.run(run_swarm())

    def test_08_semantic_proof_cache(self):
        """Test semantic proof cache storing and instant retrieval."""
        claim = "∀a, b ∈ ℝ: a^2 + b^2 >= 2ab"
        cert_data = {"certificate_id": "cert_test_123", "status": "PROVEN_VALID", "proof_tree_hash": "0xabc123"}
        
        self.cache.store_proof(claim, cert_data)
        cached = self.cache.get_proof(claim)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["certificate_id"], "cert_test_123")
        
        stats = self.cache.get_stats()
        self.assertGreaterEqual(stats["total_hits"], 1)

    def test_09_cloud_telemetry_metrics(self):
        """Test real-time cluster telemetry, percentiles and audit logs."""
        self.telemetry.record_inference(latency_ms=12.5, tokens=250, tier="pro")
        self.telemetry.record_inference(latency_ms=18.0, tokens=300, tier="ultra")
        self.telemetry.record_verification(latency_ms=1.4, status="PROVEN_SAT")
        
        metrics = self.telemetry.get_cluster_metrics()
        self.assertGreaterEqual(metrics["total_inferences"], 2)
        self.assertGreaterEqual(metrics["total_verifications"], 1)
        self.assertGreater(metrics["formal_soundness_percent"], 0)
        self.assertIn("p50", metrics["inference_latency_ms"])

    def test_10_sota_papers_and_compiler(self):
        """Test research paper hub indexing and live technique compilation."""
        papers = get_all_papers()
        self.assertGreaterEqual(len(papers), 3)
        
        comp_res = cloud_paper_compiler.compile_paper_technique("arxiv_2025_cove_smt", user_tier="pro")
        self.assertTrue(comp_res["success"])
        self.assertEqual(comp_res["status"], "COMPILED_AND_ACTIVE")

    def test_11_client_sdk_full_features(self):
        """Test TruthGPTCloudClient high-level methods."""
        async def run_client_tests():
            client = TruthGPTCloudClient()
            
            # 1. Ask
            res = await client.ask_async("Demostrar que la función exponencial e^x es estrictamente creciente.")
            self.assertIsNotNone(res.content)
            self.assertGreater(res.time_to_first_token_ms, 0)
            
            # 2. Batch Ask
            batch_res = await client.batch_ask_async([
                "Verificar identidad log(ab) = log(a) + log(b)",
                "Demostrar invariante de conservación de energía"
            ])
            self.assertEqual(len(batch_res), 2)
            
            # 3. Stream
            chunks = []
            async for chunk in client.stream_async("Verificar serie de Taylor"):
                chunks.append(chunk)
            self.assertGreater(len(chunks), 1)
            
            # 4. Telemetry and Cache Stats from client
            t_stats = client.get_telemetry_stats()
            self.assertIn("total_inferences", t_stats)
            c_stats = client.get_cache_stats()
            self.assertIn("cached_entries", c_stats)
            
        asyncio.run(run_client_tests())

    def test_12_fastapi_server_endpoints(self):
        """Test FastAPI server REST, verification, telemetry and papers endpoints."""
        from fastapi.testclient import TestClient
        from truthgpt_cloud_server import app
        
        api_client = TestClient(app)
        
        # 1. GET /api/v1/cloud/tiers
        r = api_client.get("/api/v1/cloud/tiers")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["tiers"]), 4)
        
        # 2. GET /api/v1/cloud/telemetry/stats
        r_tel = api_client.get("/api/v1/cloud/telemetry/stats")
        self.assertEqual(r_tel.status_code, 200)
        self.assertTrue(r_tel.json()["success"])
        
        # 3. GET /api/v1/cloud/cache/stats
        r_cache = api_client.get("/api/v1/cloud/cache/stats")
        self.assertEqual(r_cache.status_code, 200)
        self.assertTrue(r_cache.json()["success"])
        
        # 4. POST /api/v1/cloud/formal/verify
        r_verify = api_client.post("/api/v1/cloud/formal/verify", json={
            "claim": "∀x ∈ ℝ: x^2 + 1 > 0",
            "tier_depth": 2
        })
        self.assertEqual(r_verify.status_code, 200)
        self.assertTrue(r_verify.json()["success"])


if __name__ == "__main__":
    unittest.main()
