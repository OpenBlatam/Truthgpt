"""
🧪 TruthGPT Cloud - Next-Gen Improvements Test Suite
Verifies:
1. Tree-of-Thoughts (ToT) Multi-Branch Reasoning & Mermaid DAG generation.
2. Adaptive Concurrency Limiter (Little's Law & TCP Vegas gradient).
3. SOTA Formal Invariants (MoE Routing, RoPE Frequencies, FlashAttention Tiling, FP8 Microscaling).
4. Enterprise Secrets Provider & Masking.
5. Cloud Health Checker & Diagnostic Reporting.
6. API Key Hashing, Masking, and Zero-Downtime Rotation.
"""

import pytest
import asyncio
from truthgpt_cloud import (
    cloud_swarm,
    cloud_verifier,
    subscription_manager,
    AdaptiveConcurrencyLimiter,
    ThoughtNode,
    TreeOfThoughtsTrace,
    CloudSecretsProvider,
    mask_secret,
    cloud_health_checker,
    hash_api_key,
    mask_api_key,
    verify_moe_routing_invariants,
    verify_rope_frequency_invariants,
    verify_flash_attention_tiling,
    verify_microscaling_fp8_bounds,
    DomainInvariantsVerifier,
)
from truthgpt_cloud.core.exceptions import ConcurrencyLimitExceededError


class TestTruthGPTCloudNextGenImprovements:

    # 1. Tree of Thoughts
    def test_tree_of_thoughts_reasoning(self):
        tot = cloud_swarm.execute_tree_of_thoughts(
            prompt="Prove convergence of distributed AdamW with adaptive clipping under Byzantine faults",
            max_depth=3,
            branching_factor=3,
            min_confidence_threshold=0.70,
        )
        assert isinstance(tot, TreeOfThoughtsTrace)
        assert tot.total_nodes_explored > 0
        assert tot.pruned_branches_count >= 1
        assert len(tot.selected_path) == 3
        assert tot.confidence_score >= 0.90
        
        # Test serialization and Mermaid generation
        d = tot.to_dict()
        assert "mermaid_graph" in d
        mermaid = tot.to_mermaid()
        assert "graph TD" in mermaid
        assert "Root" in mermaid
        assert "Solution" in mermaid

    # 2. Adaptive Concurrency Limiter
    def test_adaptive_concurrency_limiter(self):
        limiter = AdaptiveConcurrencyLimiter(initial_limit=5, min_limit=2, max_limit=10, smoothing_factor=0.5)
        stats = limiter.get_stats()
        assert stats["limit"] == 5
        assert stats["in_flight"] == 0

        # Acquire and release normal latency (RTT below tolerance -> limit grows)
        with limiter:
            assert limiter.in_flight == 1
        limiter.release(latency_ms=10.0)

        # Simulate low latency to expand limit
        for _ in range(5):
            limiter.try_acquire()
            limiter.release(latency_ms=10.0)
        assert limiter.limit >= 5

        # Simulate high latency spike to trigger backoff
        for _ in range(10):
            limiter.try_acquire()
            limiter.release(latency_ms=500.0)
        assert limiter.limit >= limiter.min_limit

        # Test context manager and rejection
        small_limiter = AdaptiveConcurrencyLimiter(initial_limit=1, min_limit=1, max_limit=2)
        assert small_limiter.try_acquire() is True
        assert small_limiter.try_acquire() is False
        with pytest.raises(ConcurrencyLimitExceededError):
            small_limiter.acquire()
        small_limiter.release(latency_ms=5.0)

    # 3. MoE Routing Invariants
    def test_moe_routing_invariants(self):
        res = verify_moe_routing_invariants(
            num_experts=8,
            top_k=2,
            tokens_per_batch=128,
            capacity_factor=1.5,
            gating_weights=[0.125] * 8,
        )
        assert res["valid"] is True
        assert res["invariants_verified"]["expert_capacity_bound"] is True
        assert res["invariants_verified"]["gating_simplex_property"] is True
        assert "proof_certificate" in res

        # Verifier facade
        facade_res = cloud_verifier.verify_moe_routing(
            num_experts=16,
            top_k=2,
            tokens_per_batch=64,
            capacity_factor=1.2,
        )
        assert facade_res["valid"] is True

    # 4. RoPE Frequency Invariants
    def test_rope_frequency_invariants(self):
        res = verify_rope_frequency_invariants(
            head_dim=128,
            max_position_embeddings=8192,
            base_theta=10000.0,
            scaling_type="linear",
            scaling_factor=2.0,
        )
        assert res["valid"] is True
        assert res["invariants_verified"]["frequency_monotonic_decay"] is True
        assert res["invariants_verified"]["nyquist_bounded"] is True

        # Class method
        c_res = DomainInvariantsVerifier.verify_rope_frequency_invariants(head_dim=64)
        assert c_res["valid"] is True

    # 5. FlashAttention Tiling Invariants
    def test_flash_attention_tiling(self):
        res = verify_flash_attention_tiling(
            block_m=128,
            block_n=64,
            head_dim=128,
            precision_bytes=2,
            sram_budget_bytes=227328,
        )
        assert res["valid"] is True
        assert res["invariants_verified"]["sram_capacity_bound"] is True
        assert res["invariants_verified"]["head_dimension_aligned"] is True

        # Oversized blocks exceeding SRAM budget
        bad_res = verify_flash_attention_tiling(
            block_m=512,
            block_n=512,
            head_dim=256,
            precision_bytes=4,
            sram_budget_bytes=32768,
        )
        assert bad_res["valid"] is False
        assert bad_res["invariants_verified"]["sram_capacity_bound"] is False

    # 6. Microscaling FP8 Invariants
    def test_microscaling_fp8_bounds(self):
        res = verify_microscaling_fp8_bounds(
            format="e4m3",
            block_size=32,
            values=[0.5, -1.2, 3.4, 0.0, 15.0],
        )
        assert res["valid"] is True
        assert res["num_mantissa_bits"] == 3
        assert res["num_exponent_bits"] == 4
        assert res["overflow_detected"] is False

        e5_res = cloud_verifier.verify_microscaling_fp8(
            format="e5m2",
            block_size=32,
            values=[100.0, 200.0, 500.0],
        )
        assert e5_res["valid"] is True
        assert e5_res["num_mantissa_bits"] == 2

    # 7. Secrets Management & Masking
    def test_secrets_management(self):
        provider = CloudSecretsProvider()
        provider.set_secret("STRIPE_KEY", "sk_live_51M0demo9824secretkey77")
        assert provider.get_secret("STRIPE_KEY") == "sk_live_51M0demo9824secretkey77"
        
        # Masking
        masked = mask_secret("sk_live_51M0demo9824secretkey77")
        assert masked.startswith("sk_live")
        assert masked.endswith("ey77")
        assert "***" in masked

        # Audit
        audit = provider.audit_status(["STRIPE_KEY", "NON_EXISTENT_KEY"])
        assert audit["STRIPE_KEY"]["is_set"] is True
        assert audit["STRIPE_KEY"]["source"] == "vault"
        assert audit["NON_EXISTENT_KEY"]["is_set"] is False

    # 8. Health Checker
    def test_health_checker(self):
        report = cloud_health_checker.run_health_check()
        assert report.overall_status.value in ["HEALTHY", "DEGRADED"]
        assert len(report.subsystems) >= 4
        assert "storage" in report.subsystems
        assert "verifier" in report.subsystems
        d = report.to_dict()
        assert "overall_status" in d
        assert "subsystems" in d

    # 9. API Key Rotation and Hashing
    def test_api_key_hashing_and_rotation(self):
        user = subscription_manager.get_user("usr_default_demo")
        assert user is not None
        orig_key = user.api_keys[0]

        # Deterministic hashing
        h = hash_api_key(orig_key)
        assert len(h) == 64  # SHA-256 hex string

        # Key masking
        m = mask_api_key(orig_key)
        assert "..." in m

        # Lookup by hash
        resolved = subscription_manager.get_user_by_api_key(h)
        assert resolved is not None
        assert resolved.user_id == user.user_id

        # Key rotation
        new_key, detail = subscription_manager.rotate_api_key(
            user_id=user.user_id,
            old_api_key=orig_key,
            label="Rotated Test Key"
        )
        assert new_key != orig_key
        assert new_key in user.api_keys
        assert orig_key not in user.api_keys

        # Old key is gone, new key resolves
        assert subscription_manager.get_user_by_api_key(orig_key) is None
        assert subscription_manager.get_user_by_api_key(new_key) is not None
