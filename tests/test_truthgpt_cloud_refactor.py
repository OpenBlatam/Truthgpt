"""
🧪 Tests for TruthGPT Cloud Architecture & Package Modularization Refactor
Validates package structure, canonical subpackages, root compatibility bridges, and symbol exports.
"""

import sys
import pytest
import inspect
from pathlib import Path


class TestTruthGPTCloudRefactor:
    """Test suite validating the modular refactor of truthgpt_cloud."""

    def test_top_level_package_exports(self):
        """Verify top-level truthgpt_cloud exports all expected public APIs."""
        import truthgpt_cloud
        
        assert hasattr(truthgpt_cloud, "__version__")
        assert truthgpt_cloud.__version__ == "2.2.0-cloud"
        
        for export_name in truthgpt_cloud.__all__:
            assert hasattr(truthgpt_cloud, export_name), f"Missing export '{export_name}' in truthgpt_cloud"

    def test_canonical_subpackages_structure(self):
        """Verify all subpackages exist and have __init__.py with valid exports."""
        subpackages = [
            "truthgpt_cloud.core",
            "truthgpt_cloud.billing",
            "truthgpt_cloud.client",
            "truthgpt_cloud.routing",
            "truthgpt_cloud.storage",
            "truthgpt_cloud.swarm",
            "truthgpt_cloud.verification",
            "truthgpt_cloud.papers",
            "truthgpt_cloud.cache",
            "truthgpt_cloud.security",
            "truthgpt_cloud.telemetry",
            "truthgpt_cloud.rate_limiting",
        ]
        
        for pkg_name in subpackages:
            mod = __import__(pkg_name, fromlist=["__all__"])
            assert hasattr(mod, "__file__"), f"{pkg_name} has no file"
            if hasattr(mod, "__all__"):
                for sym in mod.__all__:
                    assert hasattr(mod, sym), f"{pkg_name} lists '{sym}' in __all__ but symbol is missing"

    def test_root_compatibility_bridges(self):
        """Verify root-level bridge modules re-export from their canonical subpackages."""
        # 1. cache
        import truthgpt_cloud.cache as cache_bridge
        from truthgpt_cloud.cache.proof_cache import CloudProofCache, proof_cache, CachedProofEntry
        assert cache_bridge.CloudProofCache is CloudProofCache
        assert cache_bridge.proof_cache is proof_cache
        assert cache_bridge.CachedProofEntry is CachedProofEntry

        # 2. security
        import truthgpt_cloud.security as sec_bridge
        from truthgpt_cloud.security.manager import CloudSecurityManager, cloud_security, ApiKeyMetadata, ApiKeyScope
        from truthgpt_cloud.security.rate_limiter import TokenBucketRateLimiter
        assert sec_bridge.CloudSecurityManager is CloudSecurityManager
        assert sec_bridge.cloud_security is cloud_security
        assert sec_bridge.ApiKeyMetadata is ApiKeyMetadata
        assert sec_bridge.ApiKeyScope is ApiKeyScope
        assert sec_bridge.TokenBucketRateLimiter is TokenBucketRateLimiter

        # 3. telemetry
        import truthgpt_cloud.telemetry as telem_bridge
        from truthgpt_cloud.telemetry.collector import CloudTelemetryCollector, cloud_telemetry, AuditLogEntry
        assert telem_bridge.CloudTelemetryCollector is CloudTelemetryCollector
        assert telem_bridge.cloud_telemetry is cloud_telemetry
        assert telem_bridge.AuditLogEntry is AuditLogEntry

        # 4. tiers
        import truthgpt_cloud.tiers as tiers_bridge
        from truthgpt_cloud.core.tiers import CloudTier, TierConfig, TIER_CONFIGURATIONS
        assert tiers_bridge.CloudTier is CloudTier
        assert tiers_bridge.TierConfig is TierConfig
        assert tiers_bridge.TIER_CONFIGURATIONS is TIER_CONFIGURATIONS

        # 5. exceptions
        import truthgpt_cloud.exceptions as exc_bridge
        from truthgpt_cloud.core.exceptions import TruthGPTCloudError, QuotaExceededError, RateLimitExceededError
        assert exc_bridge.TruthGPTCloudError is TruthGPTCloudError
        assert exc_bridge.QuotaExceededError is QuotaExceededError
        assert exc_bridge.RateLimitExceededError is RateLimitExceededError

        # 6. verifier
        import truthgpt_cloud.verifier as verifier_bridge
        from truthgpt_cloud.verification.verifier import CloudFormalVerifier, cloud_verifier
        assert verifier_bridge.CloudFormalVerifier is CloudFormalVerifier
        assert verifier_bridge.cloud_verifier is cloud_verifier

        # 7. swarm_cloud
        import truthgpt_cloud.swarm_cloud as swarm_bridge
        from truthgpt_cloud.swarm.orchestrator import CloudSwarmOrchestrator, cloud_swarm
        assert swarm_bridge.CloudSwarmOrchestrator is CloudSwarmOrchestrator
        assert swarm_bridge.cloud_swarm is cloud_swarm

        # 8. engine_router
        import truthgpt_cloud.engine_router as router_bridge
        from truthgpt_cloud.routing.router import CloudIntelligenceRouter, cloud_router
        assert router_bridge.CloudIntelligenceRouter is CloudIntelligenceRouter
        assert router_bridge.cloud_router is cloud_router

        # 9. billing
        import truthgpt_cloud.billing as billing_bridge
        from truthgpt_cloud.billing.subscription import SubscriptionManager, subscription_manager
        assert billing_bridge.SubscriptionManager is SubscriptionManager
        assert billing_bridge.subscription_manager is subscription_manager

        # 10. client
        import truthgpt_cloud.client as client_bridge
        from truthgpt_cloud.client.client import TruthGPTCloudClient
        assert client_bridge.TruthGPTCloudClient is TruthGPTCloudClient

    def test_cache_functionality(self):
        """Verify semantic proof cache functionality and warm-up."""
        from truthgpt_cloud.cache import CloudProofCache
        
        cache = CloudProofCache(max_entries=10)
        warmup_count = cache.warm_up()
        assert warmup_count >= 2
        
        stats = cache.get_stats()
        assert stats["cached_entries"] >= 2
        
        # Test hit
        proof = cache.get_proof("∀x, y ∈ ℝ: (x + y)^2 >= 4xy")
        assert proof is not None
        assert proof["status"] == "PROVEN_VALID"
        
        # Test miss
        miss = cache.get_proof("unknown random hypothesis 12345")
        assert miss is None

    def test_security_manager_functionality(self):
        """Verify security manager API key generation, validation, and revocation."""
        from truthgpt_cloud.security import CloudSecurityManager, ApiKeyScope
        
        sec = CloudSecurityManager()
        raw_key, meta = sec.generate_api_key("usr_test_refactor_123", name="Refactor Key", scopes={ApiKeyScope.VERIFY})
        assert raw_key.startswith("tgpt_cloud_live_")
        assert meta.user_id == "usr_test_refactor_123"
        
        # Validate valid key
        validated = sec.validate_api_key(raw_key, required_scope=ApiKeyScope.VERIFY)
        assert validated.key_id == meta.key_id
        
        # Revoke
        assert sec.revoke_key(meta.key_hash) is True
        with pytest.raises(Exception):
            sec.validate_api_key(raw_key)

    def test_telemetry_metrics_and_prometheus(self):
        """Verify telemetry collector metrics recording and Prometheus output."""
        from truthgpt_cloud.telemetry import CloudTelemetryCollector
        
        telem = CloudTelemetryCollector()
        telem.record_inference(latency_ms=45.2, tokens=120, tier="pro")
        telem.record_verification(latency_ms=12.1, status="PROVEN_VALID")
        telem.record_swarm()
        telem.record_audit_event("key_generated", "usr_999", {"key": "test"})
        
        metrics = telem.get_cluster_metrics()
        assert metrics["total_inferences"] >= 1
        assert metrics["total_verifications"] >= 1
        assert metrics["total_swarms"] >= 1
        assert metrics["active_audits_count"] >= 1
        
        prom_text = telem.to_prometheus_text()
        assert "truthgpt_cloud_uptime_seconds" in prom_text
        assert "truthgpt_cloud_inferences_total" in prom_text
        assert "truthgpt_cloud_verifications_total" in prom_text

    def test_client_sdk_end_to_end(self):
        """Verify TruthGPTCloudClient initialization and integrated capabilities."""
        from truthgpt_cloud import TruthGPTCloudClient, CloudTier
        
        client = TruthGPTCloudClient(tier=CloudTier.PRO)
        assert client.tier == CloudTier.PRO
        assert client.tier_config.requests_per_minute == 120
        
        # Test verification through client
        res = client.verify_claim("x + y == y + x")
        assert res.status in ("PROVEN_VALID", "VERIFIED_SYMBOLIC")
        assert res.proof_tree_hash.startswith("0x")
        
        # Test tensor verification
        t_res = client.verify_tensor_shapes(
            shape_a=[32, 128],
            shape_b=[128, 512],
            operation="matmul"
        )
        assert t_res["is_valid"] is True
        assert t_res["resulting_shape"] == [32, 512]
        
        # Test numerical stability
        s_res = client.verify_numerical_stability(
            formula_or_loss="x / (sum(x) + 1e-8)",
            gradient_clipping_bound=1.0,
            epsilon=1e-8
        )
        assert s_res["stable"] is True
