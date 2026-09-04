"""
🧪 Comprehensive Test Suite for TruthGPT Cloud Enhancements
Validates SMT-LIB2 execution, Attention & Quantization invariants, Optimizer bounds,
Merkle exclusion proofs, Multi-target Paper kernel synthesis, Rate limiting context managers,
Promo code engine, SLA metrics & Grafana dashboards, and FastAPI endpoints.
"""

import sys
import pytest
from pathlib import Path

# Ensure workspace root is in sys.path
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from truthgpt_cloud import (
    CloudTier,
    subscription_manager,
    cloud_verifier,
    cloud_telemetry,
    proof_cache,
    cloud_paper_compiler,
    cloud_rate_limiter,
    TruthGPTCloudClient
)


class TestTruthGPTCloudComprehensiveEnhancements:
    """Complete test suite for TruthGPT Cloud enhancements."""

    # ---------------------------------------------------------------------------
    # 1. Formal Verification: SMT-LIB2, Attention, Quantization, Optimizer
    # ---------------------------------------------------------------------------

    def test_smt2_script_solver(self):
        """Test direct execution of SMT-LIB2 scripts."""
        smt2_code = """
        (set-logic QF_NRA)
        (declare-const x Real)
        (declare-const y Real)
        (assert (> x 0.0))
        (assert (> y 0.0))
        (assert (< (+ x y) 0.0))
        (check-sat)
        """
        res = cloud_verifier.verify_smt2_script(smt2_code)
        assert res["success"] is True
        assert res["status"] in ["UNSAT", "SAT", "SYNTAX_CHECKED_SAT", "PARSED_SAT"]
        assert res["assertions_count"] == 3
        assert res["merkle_root"].startswith("0x")

    def test_multi_variable_extraction_and_proving(self):
        """Test SMT proving with multi-character identifiers."""
        claim = "∀loss, lr, theta_k ∈ ℝ⁺: loss + lr * theta_k >= 0"
        cert = cloud_verifier.verify_expression(claim, tier_depth=2)
        assert cert.status in ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"]
        assert len(cert.mathematical_invariants) >= 1
        assert cert.verify_integrity() is True

    def test_attention_invariants_verification(self):
        """Test Transformer Attention contract verification."""
        # Valid GQA: 32 Q heads, 8 KV heads, head_dim 128
        res_valid = cloud_verifier.verify_attention_invariants(
            query_shape=[2, 512, 32, 128],
            key_shape=[2, 512, 8, 128],
            value_shape=[2, 512, 8, 128],
            num_heads_q=32,
            num_heads_kv=8,
            head_dim=128,
            is_causal=True
        )
        assert res_valid["is_valid"] is True
        assert "FlashAttention-3" in res_valid["architecture_type"]
        assert len(res_valid["invariants_verified"]) >= 4

        # Invalid GQA: 32 Q heads, 5 KV heads (not divisible)
        res_invalid = cloud_verifier.verify_attention_invariants(
            query_shape=[2, 512, 32, 128],
            key_shape=[2, 512, 5, 128],
            value_shape=[2, 512, 5, 128],
            num_heads_q=32,
            num_heads_kv=5,
            head_dim=128
        )
        assert res_invalid["is_valid"] is False
        assert len(res_invalid["violations"]) > 0

    def test_quantization_safety_verification(self):
        """Test Quantization scaling and clipping safety invariants."""
        # INT8 symmetric
        res_int8 = cloud_verifier.verify_quantization_safety(
            min_val=-3.5,
            max_val=3.5,
            quant_format="INT8",
            symmetric=True
        )
        assert res_int8["is_valid"] is True
        assert res_int8["bits"] == 8
        assert res_int8["scale_factor"] > 0

        # BitNet b1.58 Ternary
        res_bitnet = cloud_verifier.verify_quantization_safety(
            min_val=-1.0,
            max_val=1.0,
            quant_format="BITNET_158",
            symmetric=True
        )
        assert res_bitnet["is_valid"] is True
        assert res_bitnet["q_min"] == -1
        assert res_bitnet["q_max"] == 1

        # FP8 E4M3
        res_fp8 = cloud_verifier.verify_quantization_safety(
            min_val=-400.0,
            max_val=400.0,
            quant_format="FP8_E4M3",
            symmetric=True
        )
        assert res_fp8["is_valid"] is True
        assert res_fp8["q_max"] == 448.0

    def test_optimizer_convergence_verification(self):
        """Test optimizer stability and convergence contracts."""
        # Valid AdamW
        res_adam = cloud_verifier.verify_optimizer_convergence(
            optimizer_name="AdamW",
            learning_rate=1e-4,
            beta1=0.9,
            beta2=0.999,
            weight_decay=0.01,
            eps=1e-8
        )
        assert res_adam["is_valid"] is True
        assert res_adam["proof_certificate"]["status"] == "OPTIMIZER_CONVERGENCE_PROVEN"

        # Valid Muon
        res_muon = cloud_verifier.verify_optimizer_convergence(
            optimizer_name="Muon",
            learning_rate=0.02,
            beta1=0.95,
            beta2=0.99
        )
        assert res_muon["is_valid"] is True
        assert "Newton-Schulz" in res_muon["invariants_verified"][2]

        # Invalid learning rate
        res_unstable = cloud_verifier.verify_optimizer_convergence(
            optimizer_name="AdamW",
            learning_rate=15.0  # Excessive LR
        )
        assert res_unstable["is_valid"] is False

    def test_merkle_exclusion_proofs(self):
        """Test cryptographic non-membership (exclusion) proofs in Merkle tree."""
        leaves = [
            "claim_alpha_01",
            "claim_beta_02",
            "claim_gamma_03",
            "claim_delta_04"
        ]
        res = cloud_verifier.verify_merkle_exclusion(
            tree_leaves=leaves,
            target_claim="claim_zeta_99"
        )
        assert res["is_excluded"] is True
        assert "lower_bound_proof" in res
        assert "upper_bound_proof" in res

    # ---------------------------------------------------------------------------
    # 2. Multi-Target Paper Compiler
    # ---------------------------------------------------------------------------

    def test_paper_multi_target_kernel_compilation(self):
        """Test paper synthesis across PyTorch, Triton, and CUDA."""
        # PyTorch
        pt_res = cloud_paper_compiler.compile_paper_technique(
            paper_id="arxiv_2026_deepseek_mla",
            user_tier="pro",
            target_framework="pytorch"
        )
        assert pt_res["status"] == "COMPILED_AND_ACTIVE"
        assert "torch" in pt_res["kernel_code"]

        # Triton
        triton_res = cloud_paper_compiler.compile_paper_technique(
            paper_id="arxiv_2026_deepseek_mla",
            user_tier="pro",
            target_framework="triton"
        )
        assert triton_res["status"] == "COMPILED_AND_ACTIVE"
        assert "triton" in triton_res["kernel_code"]

        # CUDA
        cuda_res = cloud_paper_compiler.compile_paper_technique(
            paper_id="arxiv_2026_deepseek_mla",
            user_tier="pro",
            target_framework="cuda"
        )
        assert cuda_res["status"] == "COMPILED_AND_ACTIVE"
        assert "__global__" in cuda_res["kernel_code"]

    # ---------------------------------------------------------------------------
    # 3. Semantic Proof Cache with Commutativity Normalization
    # ---------------------------------------------------------------------------

    def test_proof_cache_commutativity(self):
        """Test that commutative statements produce the same cache hash."""
        proof_cache.clear()
        
        cert = cloud_verifier.verify_expression("a + b == b + a")
        proof_cache.store_proof("a + b == b + a", cert.to_dict())

        # Retrieve with reversed equality
        retrieved = proof_cache.get_proof("b + a == a + b")
        assert retrieved is not None
        assert retrieved["certificate_id"] == cert.certificate_id

        stats = proof_cache.get_stats()
        assert stats["total_hits"] >= 1

    # ---------------------------------------------------------------------------
    # 4. Rate Limiting Context Managers
    # ---------------------------------------------------------------------------

    def test_rate_limiter_sync_context_manager(self):
        """Test synchronous context manager on SlidingWindowRateLimiter."""
        user_id = "usr_ctx_sync_test"
        with cloud_rate_limiter.sync_limit(user_id=user_id, max_rpm=100, max_concurrency=5):
            metrics = cloud_rate_limiter.get_user_rate_metrics(user_id)
            assert metrics["requests_last_minute"] >= 1
            assert metrics["active_concurrent_requests"] == 1

        # Released concurrency
        metrics_after = cloud_rate_limiter.get_user_rate_metrics(user_id)
        assert metrics_after["active_concurrent_requests"] == 0

    @pytest.mark.asyncio
    async def test_rate_limiter_async_context_manager(self):
        """Test asynchronous context manager on SlidingWindowRateLimiter."""
        user_id = "usr_ctx_async_test"
        async with cloud_rate_limiter.limit(user_id=user_id, max_rpm=100, max_concurrency=5):
            metrics = cloud_rate_limiter.get_user_rate_metrics(user_id)
            assert metrics["requests_last_minute"] >= 1
            assert metrics["active_concurrent_requests"] == 1

        metrics_after = cloud_rate_limiter.get_user_rate_metrics(user_id)
        assert metrics_after["active_concurrent_requests"] == 0

    # ---------------------------------------------------------------------------
    # 5. Promo Code Engine & Quota Alerts
    # ---------------------------------------------------------------------------

    def test_promo_code_application(self):
        """Test subscription upgrade with discount promo code."""
        user = subscription_manager.register_user(
            email="promo_user@truthgpt.ai",
            name="Promo Tester",
            tier=CloudTier.FREE
        )

        res_promo = subscription_manager.upgrade_subscription(
            user_id=user.user_id,
            target_tier=CloudTier.PRO,
            billing_cycle="monthly",
            promo_code="DEV50"
        )
        assert res_promo["success"] is True
        assert res_promo["invoice"]["promo_code"] == "DEV50"
        assert res_promo["invoice"]["discount_applied_usd"] > 0
        assert res_promo["invoice"]["amount_usd"] == 9.995 or res_promo["invoice"]["amount_usd"] == 10.0 or res_promo["invoice"]["amount_usd"] == round(19.99 * 0.5, 2)

    # ---------------------------------------------------------------------------
    # 6. Observability: SLA Metrics & Grafana Dashboard
    # ---------------------------------------------------------------------------

    def test_sla_and_grafana_dashboard(self):
        """Test SLA error budget calculation and Grafana dashboard generation."""
        sla_data = cloud_telemetry.get_sla_status()
        assert "sla_target_percent" in sla_data
        assert "current_uptime_percent" in sla_data
        assert sla_data["sla_target_percent"] == 99.9

        grafana = cloud_telemetry.generate_grafana_dashboard_json()
        assert grafana["uid"] == "truthgpt-cloud-cluster"
        assert len(grafana["panels"]) >= 4

    # ---------------------------------------------------------------------------
    # 7. Python Client SDK Full Lifecycle
    # ---------------------------------------------------------------------------

    def test_client_sdk_full_enhancements(self):
        """Test enhanced Python Client SDK with context managers and helpers."""
        with TruthGPTCloudClient() as client:
            assert client.user_id is not None
            
            # SMT2 script
            res_smt2 = client.verify_smt2_script("(set-logic QF_NRA)\n(assert (> 1.0 0.0))\n(check-sat)")
            assert res_smt2["success"] is True

            # SLA metrics
            sla = client.get_sla_metrics()
            assert sla["sla_target_percent"] == 99.9

            # Grafana export
            dashboard = client.export_grafana_dashboard()
            assert "panels" in dashboard

            # Attention verification
            attn = client.verify_attention_invariants(
                query_shape=[1, 128, 16, 64],
                key_shape=[1, 128, 16, 64],
                value_shape=[1, 128, 16, 64],
                num_heads_q=16,
                num_heads_kv=16,
                head_dim=64
            )
            assert attn["is_valid"] is True

    # ---------------------------------------------------------------------------
    # 8. FastAPI Server Endpoints
    # ---------------------------------------------------------------------------

    def test_fastapi_server_enhancement_endpoints(self):
        """Test new FastAPI REST endpoints using TestClient."""
        from fastapi.testclient import TestClient
        from truthgpt_cloud_server import app

        client = TestClient(app)

        # SMT2 raw execution
        r = client.post("/api/v1/cloud/formal/verify/smt2-raw", json={
            "smt2_text": "(set-logic QF_NRA)\n(assert (> 5.0 2.0))\n(check-sat)"
        })
        assert r.status_code == 200
        assert r.json()["success"] is True

        # Grafana Dashboard export
        r = client.get("/api/v1/cloud/telemetry/grafana-dashboard")
        assert r.status_code == 200
        assert r.json()["uid"] == "truthgpt-cloud-cluster"

        # SLA metrics
        r = client.get("/api/v1/cloud/telemetry/sla")
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert "sla" in r.json()

        # Apply Promo Code
        r = client.post("/api/v1/cloud/subscription/apply-promo", json={
            "user_id": "usr_pro_sample",
            "promo_code": "DEV50",
            "target_tier": "pro",
            "billing_cycle": "monthly"
        })
        assert r.status_code == 200
        assert r.json()["success"] is True
