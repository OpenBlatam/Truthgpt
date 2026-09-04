"""
🧪 Unit Test Suite for Refactored TruthGPT Cloud Subpackages & Bridges
Validates modularization of core, security, cache, telemetry, storage, billing,
verification, swarm, routing, papers, and client SDK.
"""

import sys
import os
import pytest
from pathlib import Path

# Ensure paths
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


class TestTruthGPTCloudModularRefactor:
    """Test suite for refactored truthgpt_cloud architecture."""

    def test_01_core_subpackage(self):
        """Test truthgpt_cloud.core constants, tiers, and exceptions."""
        from truthgpt_cloud.core import (
            CLOUD_PLATFORM_VERSION,
            CloudTier,
            get_tier_config,
            get_all_tiers,
            TruthGPTCloudError,
            QuotaExceededError,
        )
        assert CLOUD_PLATFORM_VERSION == "2.2.0-cloud"
        assert len(get_all_tiers()) == 4
        
        pro_cfg = get_tier_config(CloudTier.PRO)
        assert pro_cfg.tier_id == CloudTier.PRO
        assert pro_cfg.requests_per_minute == 120
        assert pro_cfg.smt_z3_verification_depth == 2

        # Exception check
        err = QuotaExceededError(message="Quota hit", limit=1000, consumed=1000)
        assert err.status_code == 402
        assert isinstance(err, TruthGPTCloudError)

    def test_02_security_subpackage(self):
        """Test truthgpt_cloud.security rate limiters, API keys, and RBAC."""
        from truthgpt_cloud.security import (
            CloudSecurityManager,
            ApiKeyScope,
            TokenBucketRateLimiter,
            SlidingWindowRateLimiter,
        )

        sm = CloudSecurityManager()
        raw_key, meta = sm.generate_api_key(
            user_id="usr_test_security",
            name="Security Test Key",
            scopes={ApiKeyScope.INFERENCE, ApiKeyScope.VERIFY}
        )
        assert raw_key.startswith("tgpt_cloud_live_")
        assert meta.user_id == "usr_test_security"
        assert meta.is_active is True

        # Validation
        validated = sm.validate_api_key(raw_key, required_scope=ApiKeyScope.INFERENCE)
        assert validated.key_id == meta.key_id

        # Token Bucket
        tb = TokenBucketRateLimiter()
        assert tb.check_rate_limit("usr_test_security", "pro", cost=1.0) is True
        assert tb.check_and_consume("usr_test_security", rpm_capacity=60, cost=1.0) is True

        # Sliding Window
        sw = SlidingWindowRateLimiter()
        assert sw.check_and_record("usr_test_security", max_rpm=100) is True
        metrics = sw.get_user_rate_metrics("usr_test_security")
        assert metrics["requests_last_minute"] == 1

    def test_03_cache_subpackage(self):
        """Test truthgpt_cloud.cache semantic proof caching and warmups."""
        from truthgpt_cloud.cache import (
            CloudProofCache,
        )

        cache = CloudProofCache(max_entries=50)
        warmed = cache.warm_up()
        assert warmed >= 2

        # Check retrieval of warmed theorem
        proof = cache.get_proof("∀x, y ∈ ℝ: (x + y)^2 >= 4xy")
        assert proof is not None
        assert proof["status"] == "PROVEN_VALID"

        stats = cache.get_stats()
        assert stats["total_hits"] >= 1
        assert stats["cached_entries"] >= 2

    def test_04_telemetry_subpackage(self):
        """Test truthgpt_cloud.telemetry collector and Prometheus exporter."""
        from truthgpt_cloud.telemetry import (
            CloudTelemetryCollector,
        )

        tel = CloudTelemetryCollector()
        tel.record_inference(latency_ms=12.5, tokens=200, tier="pro")
        tel.record_inference(latency_ms=25.0, tokens=400, tier="pro")
        tel.record_verification(latency_ms=3.5, status="PROVEN_VALID")
        tel.record_swarm()
        tel.record_audit_event("key_created", "usr_telemetry_test", {"key_id": "key_123"})

        metrics = tel.get_cluster_metrics()
        assert metrics["total_inferences"] == 2
        assert metrics["total_verifications"] == 1
        assert metrics["total_swarms"] == 1
        assert metrics["inference_latency_ms"]["avg"] == 18.75

        prom_text = tel.to_prometheus_text()
        assert "truthgpt_cloud_inferences_total 2" in prom_text
        assert "truthgpt_cloud_verifications_total 1" in prom_text

    def test_05_storage_subpackage(self, tmp_path):
        """Test truthgpt_cloud.storage atomic JSON file storage backend."""
        from truthgpt_cloud.storage import (
            JsonFileStorageBackend,
        )

        test_file = str(tmp_path / "test_store.json")
        storage = JsonFileStorageBackend(test_file)
        storage.set("users", "usr_1", {"name": "Alice", "tier": "pro"})
        storage.set("users", "usr_2", {"name": "Bob", "tier": "ultra"})

        assert storage.get("users", "usr_1")["name"] == "Alice"
        assert len(storage.get_all("users")) == 2

        # Snapshot
        snap = storage.create_snapshot()
        assert os.path.exists(snap)

    def test_06_billing_subpackage(self):
        """Test truthgpt_cloud.billing manager, payment gateway, and webhooks."""
        from truthgpt_cloud.billing import (
            PaymentGatewayService,
            WebhookManager,
        )

        # Gateway
        pay_res = PaymentGatewayService.process_payment(
            user_id="usr_bill_test",
            amount_usd=19.99,
            tier_id="pro",
            payment_method="crypto_usdc"
        )
        assert pay_res["success"] is True
        assert pay_res["metadata"]["asset"] == "USDC"

        # Webhook
        wm = WebhookManager()
        sub = wm.register_webhook("usr_bill_test", "https://api.example.com/webhook")
        assert sub.target_url == "https://api.example.com/webhook"
        evt = wm.emit_event("subscription.upgraded", "usr_bill_test", {"tier": "pro"})
        assert evt.signature.startswith("sha256=")

    def test_07_verification_subpackage(self):
        """Test truthgpt_cloud.verification formal solver and certificate exports."""
        from truthgpt_cloud.verification import (
            CloudFormalVerifier,
            verify_proof_certificate,
        )

        verifier = CloudFormalVerifier()
        cert = verifier.verify_expression("∀a,b: a^2 - b^2 = (a-b)(a+b)", tier_depth=2)
        assert cert.status in ["PROVEN_VALID", "VERIFIED_SYMBOLIC"]
        assert verify_proof_certificate(cert) is True

        # Exporters
        lean_code = cert.to_lean4_script()
        assert "theorem" in lean_code
        coq_code = cert.to_coq_script()
        assert "Lemma" in coq_code
        smt2_code = cert.to_smt2_script()
        assert "(set-logic QF_NRA)" in smt2_code
        jsonld = cert.to_jsonld()
        assert "FormalProofCertificate" in jsonld["type"]

        # Tensor shapes
        t_res = verifier.verify_tensor_shapes([32, 128], [128, 64], operation="matmul")
        assert t_res["is_valid"] is True
        assert t_res["output_shape"] == [32, 64]

    @pytest.mark.asyncio
    async def test_08_swarm_and_routing_subpackages(self):
        """Test truthgpt_cloud.swarm and truthgpt_cloud.routing."""
        from truthgpt_cloud.swarm import CloudSwarmOrchestrator
        from truthgpt_cloud.routing import CloudIntelligenceRouter

        swarm = CloudSwarmOrchestrator()
        trace = await swarm.execute_swarm_session("Optimize CUDA kernel for FlashAttention", max_agents=3)
        assert trace.session_id.startswith("swarm_sess_")
        assert len(trace.agents_involved) == 3

        router = CloudIntelligenceRouter()
        resp = await router.route_inference(
            prompt="Analyze polynomial stability",
            user_id="usr_default_demo",
            enable_formal_verification=True
        )
        assert resp.response_id.startswith("resp_tgpt_")
        assert resp.verification_passed is True

    def test_09_papers_and_client_sdk(self):
        """Test truthgpt_cloud.papers and truthgpt_cloud.client."""
        from truthgpt_cloud.papers import (
            get_all_papers,
            CloudPaperCompiler,
        )
        from truthgpt_cloud.client import TruthGPTCloudClient

        papers = get_all_papers()
        assert len(papers) >= 5
        comp_res = CloudPaperCompiler.compile_paper_technique("arxiv_2026_flash_attn_3", user_tier="pro")
        assert comp_res["status"] == "COMPILED_AND_ACTIVE"

        client = TruthGPTCloudClient()
        stat = client.get_subscription_status()
        assert "tier" in stat
        cert = client.verify_claim("x + y >= 0")
        assert cert.proof_tree_hash is not None

    def test_10_backward_compatibility_bridges(self):
        """Test all 11 top-level bridge files."""
        import truthgpt_cloud.billing as b_bridge
        import truthgpt_cloud.cache as c_bridge
        import truthgpt_cloud.client as cl_bridge
        import truthgpt_cloud.engine_router as er_bridge
        import truthgpt_cloud.exceptions as ex_bridge
        import truthgpt_cloud.rate_limiter as rl_bridge
        import truthgpt_cloud.security as sec_bridge
        import truthgpt_cloud.swarm_cloud as sc_bridge
        import truthgpt_cloud.telemetry as tel_bridge
        import truthgpt_cloud.tiers as t_bridge
        import truthgpt_cloud.verifier as v_bridge

        assert hasattr(b_bridge, "SubscriptionManager")
        assert hasattr(c_bridge, "CloudProofCache")
        assert hasattr(cl_bridge, "TruthGPTCloudClient")
        assert hasattr(er_bridge, "CloudIntelligenceRouter")
        assert hasattr(ex_bridge, "QuotaExceededError")
        assert hasattr(rl_bridge, "SlidingWindowRateLimiter")
        assert hasattr(sec_bridge, "CloudSecurityManager")
        assert hasattr(sc_bridge, "CloudSwarmOrchestrator")
        assert hasattr(tel_bridge, "CloudTelemetryCollector")
        assert hasattr(t_bridge, "CloudTier")
        assert hasattr(v_bridge, "CloudFormalVerifier")

        # Deep parity checks for harmonized bridge exports
        assert hasattr(sec_bridge, "LedgerBlock")
        assert hasattr(sec_bridge, "cloud_rate_limiter")
        assert hasattr(sec_bridge, "token_bucket_limiter")
        assert hasattr(sec_bridge, "rate_limiter")
        assert hasattr(b_bridge, "TOKEN_PACK_CATALOG")
        assert hasattr(b_bridge, "SlidingWindowRateLimiter")
        assert hasattr(b_bridge, "ConcurrencyLimitExceededError")
        assert hasattr(tel_bridge, "AlertRule")
        assert hasattr(v_bridge, "verify_merkle_inclusion")
        assert hasattr(sc_bridge, "get_adversarial_team_nodes")

    def test_11_optimization_core_lazy_imports(self):
        """Test lazy loading of TruthGPT Cloud components directly from optimization_core."""
        import optimization_core

        # Verify key cloud exports are accessible lazily
        assert optimization_core.TruthGPTCloudClient is not None
        assert optimization_core.CloudTier is not None
        assert optimization_core.cloud_verifier is not None
        assert optimization_core.cloud_swarm is not None
        assert optimization_core.cloud_router is not None
        assert optimization_core.cloud_telemetry is not None
        assert optimization_core.proof_cache is not None
        assert optimization_core.subscription_manager is not None
        assert optimization_core.cloud_security is not None
        assert optimization_core.CircuitBreaker is not None
        assert optimization_core.AlertRule is not None
        assert optimization_core.RateLimitExceededError is not None

        # Verify __dir__ includes truthgpt_cloud symbols
        attrs = dir(optimization_core)
        assert "TruthGPTCloudClient" in attrs
        assert "CloudTier" in attrs
        assert "cloud_verifier" in attrs
        assert "cloud_swarm" in attrs
        assert "CircuitBreaker" in attrs
        assert "AlertRule" in attrs

    def test_12_core_types_and_exports(self):
        """Test unified core types exported from truthgpt_cloud, .core, and lazy loader."""
        from truthgpt_cloud import (
            CloudFeature,
            VerificationEngineType,
            ProofStatus,
            SwarmTopologyType,
            PaymentMethodType,
            AlertComparisonOp,
        )
        from truthgpt_cloud.core import (
            CloudFeature as CoreFeature,
            VerificationEngineType as CoreEngine,
            ProofStatus as CoreStatus,
            SwarmTopologyType as CoreTopology,
        )
        import optimization_core

        assert CloudFeature.FORMAL_VERIFICATION == "formal_verification"
        assert CoreFeature.SWARM_ORCHESTRATION == "swarm_orchestration"
        assert VerificationEngineType.Z3_SMT == "z3_smt"
        assert CoreEngine.LEAN4 == "lean4"
        assert ProofStatus.PROVEN_VALID == "PROVEN_VALID"
        assert CoreStatus.SAT == "SAT"
        assert SwarmTopologyType.HIERARCHICAL == "hierarchical"
        assert CoreTopology.MESH == "mesh"
        assert PaymentMethodType.STRIPE_CARD == "stripe_card"
        assert AlertComparisonOp.GTE == "gte"

        # Lazy imports through optimization_core
        assert optimization_core.CloudFeature is not None
        assert optimization_core.VerificationEngineType is not None
        assert optimization_core.ProofStatus is not None
        assert optimization_core.get_topology_metrics is not None

    def test_13_storage_path_env_override(self, tmp_path):
        """Test TRUTHGPT_STORAGE_PATH environment variable override."""
        import os
        from truthgpt_cloud.billing.subscription import SubscriptionManager

        custom_db = str(tmp_path / "custom_test_subscriptions.json")
        old_val = os.environ.get("TRUTHGPT_STORAGE_PATH")
        try:
            os.environ["TRUTHGPT_STORAGE_PATH"] = custom_db
            mgr = SubscriptionManager()
            assert os.path.abspath(mgr.storage_path) == os.path.abspath(custom_db)
            assert os.path.exists(custom_db)
        finally:
            if old_val is None:
                os.environ.pop("TRUTHGPT_STORAGE_PATH", None)
            else:
                os.environ["TRUTHGPT_STORAGE_PATH"] = old_val

    def test_14_client_sdk_tier_resolution(self):
        """Test TruthGPTCloudClient resolves correct starter user when tier is specified."""
        from truthgpt_cloud import TruthGPTCloudClient, CloudTier

        pro_client = TruthGPTCloudClient(tier=CloudTier.PRO)
        assert pro_client.tier == CloudTier.PRO

        ultra_client = TruthGPTCloudClient(tier=CloudTier.ULTRA)
        assert ultra_client.tier == CloudTier.ULTRA

        free_client = TruthGPTCloudClient(tier=CloudTier.FREE)
        assert free_client.tier == CloudTier.FREE



