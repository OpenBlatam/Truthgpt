"""
🧪 TruthGPT Cloud - Unit Tests for Redis L2 Cache, Structlog, Rich UI, and Theorem Synthesis
Verifies:
  1. RedisProofCacheBackend (xxhash, zstd, orjson, connection pooling & offline fallback)
  2. RedisSlidingWindowRateLimiter & RedisTokenBucketRateLimiter
  3. Structlog enterprise structured JSON logging
  4. Rich terminal panels & cluster status tables
  5. Lean 4 / Coq automated proof synthesis
  6. Python AST code purity & mathematical invariant verification
  7. FastAPI server endpoints for theorem synthesis, purity, and cluster cache
"""

import pytest
from unittest.mock import MagicMock

from truthgpt_cloud import (
    CloudTier,
    cloud_verifier,
    proof_cache,
    cloud_telemetry,
    RedisProofCacheBackend,
    RedisSlidingWindowRateLimiter,
    RedisTokenBucketRateLimiter,
    get_cloud_logger,
    configure_structured_logging,
    render_certificate_panel,
    render_cluster_status_table,
    render_tier_comparison_table,
)
from truthgpt_cloud.cache.proof_cache import CloudProofCache


# ============================================================================
# 1. ⚡ Redis Proof Cache Backend Tests
# ============================================================================

class TestRedisProofCacheBackend:

    def test_01_redis_backend_instantiation_and_key_computation(self):
        backend = RedisProofCacheBackend(redis_url="redis://localhost:6379/15")
        assert backend.key_prefix == "truthgpt:proof:"
        key = backend.compute_key("x + y == y + x")
        assert key.startswith("truthgpt:proof:")
        assert len(key) > len("truthgpt:proof:")

    def test_02_redis_backend_offline_graceful_fallback(self):
        backend = RedisProofCacheBackend(redis_url="redis://127.0.0.1:59999/0")
        assert not backend.is_connected
        # Offline gets, sets, deletes should return gracefully without crashing
        assert backend.get_proof("x == x") is None
        assert backend.set_proof("x == x", {"status": "VALID"}) is False
        assert backend.delete_proof("x == x") is False
        assert backend.clear() == 0
        stats = backend.get_stats()
        assert stats["is_connected"] is False

    def test_03_redis_backend_mocked_roundtrip_with_compression(self):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        store = {}

        def mock_setex(k, ttl, v):
            store[k] = v
            return True

        def mock_get(k):
            return store.get(k)

        mock_redis.setex.side_effect = mock_setex
        mock_redis.get.side_effect = mock_get

        backend = RedisProofCacheBackend(client=mock_redis, compress_threshold=10)
        assert backend.is_connected is True

        payload = {
            "certificate_id": "cert_mock_999",
            "theorem_or_claim": "∀x,y ∈ ℝ⁺: (x+y)/2 ≥ √(x*y)",
            "status": "PROVEN_VALID",
            "proof_tree_hash": "0xabcdef1234567890",
            "proof_steps": ["Paso 1: AM-GM Invariant", "Paso 2: QED"],
            "mathematical_invariants": ["AM-GM bound holds for all positive reals"]
        }

        saved = backend.set_proof("am_gm_theorem", payload, ttl_seconds=3600)
        assert saved is True
        assert mock_redis.setex.called

        retrieved = backend.get_proof("am_gm_theorem")
        assert retrieved is not None
        assert retrieved["certificate_id"] == "cert_mock_999"
        assert retrieved["status"] == "PROVEN_VALID"

    def test_04_cloud_proof_cache_l2_integration(self):
        mock_backend = MagicMock()
        mock_backend.is_connected = True
        mock_backend.get_proof.return_value = {
            "certificate_id": "l2_cert_123",
            "theorem_or_claim": "x^2 + 1 > 0",
            "status": "PROVEN_VALID",
            "proof_tree_hash": "0x1234",
            "proof_steps": ["Step 1"],
            "mathematical_invariants": ["x^2 >= 0"],
            "confidence_score": 1.0,
        }
        mock_backend.get_stats.return_value = {"backend": "redis_l2", "hits": 1}

        cache = CloudProofCache(redis_backend=mock_backend, auto_warmup=False)
        cert_data = cache.get_proof("x^2 + 1 > 0")
        assert cert_data is not None
        assert cert_data["certificate_id"] == "l2_cert_123"
        # Second access should hit L1 in memory
        cert_data_l1 = cache.get_proof("x^2 + 1 > 0")
        assert cert_data_l1 is not None
        assert cache._total_hits >= 2


# ============================================================================
# 2. ⏱️ Redis Rate Limiter Tests
# ============================================================================

class TestRedisRateLimiting:

    def test_01_redis_sliding_window_fallback_when_offline(self):
        limiter = RedisSlidingWindowRateLimiter(redis_url="redis://127.0.0.1:59999/0")
        assert not limiter.is_connected
        # Uses local fallback
        res = limiter.check_rate_limit("test_user_offline", CloudTier.PRO)
        assert res is True

    def test_02_redis_token_bucket_fallback_when_offline(self):
        limiter = RedisTokenBucketRateLimiter(redis_url="redis://127.0.0.1:59999/0")
        assert not limiter.is_connected
        res = limiter.check_rate_limit("test_user_tb_offline", CloudTier.ENTERPRISE, cost=2.0)
        assert res is True

    def test_03_redis_sliding_window_mocked_redis_pipeline(self):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_pipe = MagicMock()
        # Results: [zremrangebyscore, zcard, zrange]
        mock_pipe.execute.return_value = [0, 5, []]
        mock_redis.pipeline.return_value = mock_pipe

        limiter = RedisSlidingWindowRateLimiter(client=mock_redis)
        assert limiter.is_connected is True

        allowed = limiter.check_rate_limit("user_mock_pipe", CloudTier.PRO)
        assert allowed is True
        assert mock_redis.pipeline.called


# ============================================================================
# 3. 📊 Structured Logging Tests
# ============================================================================

class TestStructuredLogging:

    def test_01_structured_logging_configuration(self):
        configure_structured_logging(log_format="json")
        logger = get_cloud_logger("TruthGPT.Test")
        assert logger is not None

    def test_02_get_cloud_logger_and_context_binding(self):
        logger = get_cloud_logger("TruthGPT.Verifier", tenant_id="org_alpha", tier="enterprise")
        assert logger is not None
        # Should execute without error
        logger.info("smt_check_dispatched", theorem="x == x", solver="z3")

    def test_03_telemetry_collector_structured_log_emission(self):
        collector = cloud_telemetry
        # Record inference, verification, swarm, and audit
        collector.record_inference(latency_ms=12.5, tokens=250, tier="pro")
        collector.record_verification(latency_ms=3.4, status="PROVEN_VALID")
        collector.record_swarm()
        collector.record_audit_event("key_generated", "user_123", {"scope": "read"})
        metrics = collector.get_metrics()
        assert metrics["total_inferences"] > 0
        assert metrics["total_verifications"] > 0


# ============================================================================
# 4. 🎨 Rich UI & Diagnostics Tests
# ============================================================================

class TestRichDiagnostics:

    def test_01_render_certificate_panel(self):
        cert = cloud_verifier.verify_expression("x + y == y + x")
        panel = render_certificate_panel(cert)
        assert panel is not None

    def test_02_render_cluster_status_table(self):
        table = render_cluster_status_table(cloud_telemetry, proof_cache)
        assert table is not None

    def test_03_render_tier_comparison_table(self):
        table = render_tier_comparison_table()
        assert table is not None


# ============================================================================
# 5. 🔬 Formal Proof Synthesis & AST Purity Tests
# ============================================================================

class TestTheoremSynthesisAndASTPurity:

    def test_01_lean4_and_coq_synthesis_on_proof_certificate(self):
        cert = cloud_verifier.verify_expression("x^2 + y^2 >= 2*x*y")
        assert cert.status in ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"]
        assert cert.lean4_proof is not None
        assert "theorem" in cert.lean4_proof or "Mathlib" in cert.lean4_proof
        assert cert.coq_proof is not None
        assert "Lemma" in cert.coq_proof or "Require Import Reals" in cert.coq_proof

    def test_02_code_purity_verification_pure_code(self):
        pure_code = """
def dot_product(a, b):
    total = 0.0
    for x, y in zip(a, b):
        total += x * y
    return total
"""
        result = cloud_verifier.verify_code_purity_and_invariants(pure_code)
        assert result["success"] is True
        assert result["is_pure"] is True
        assert len(result["violations"]) == 0
        assert "dot_product" in result["functions_found"]

    def test_03_code_purity_verification_hazard_detection(self):
        hazardous_code = """
import os
import subprocess

def dangerous_run(cmd):
    eval("print('exploited')")
    open('/etc/passwd', 'r')
    return os.system(cmd)
"""
        result = cloud_verifier.verify_code_purity_and_invariants(hazardous_code)
        assert result["success"] is True
        assert result["is_pure"] is False
        assert len(result["violations"]) >= 3
        # Should flag os import, eval, open
        v_str = " ".join(result["violations"])
        assert "os" in v_str
        assert "eval" in v_str or "open" in v_str


# ============================================================================
# 6. 🚀 FastAPI Server Endpoints Tests
# ============================================================================

class TestFastAPINewEndpoints:

    @pytest.fixture
    def client(self):
        from starlette.testclient import TestClient
        from truthgpt_cloud_server import app
        return TestClient(app)

    def test_01_code_purity_endpoint(self, client):
        resp = client.post(
            "/api/v1/cloud/formal/verify/code-purity",
            json={"code": "def square(x):\n    return x * x\n"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_pure"] is True

    def test_02_synthesize_theorem_endpoint(self, client):
        resp = client.post(
            "/api/v1/cloud/formal/synthesize-theorem",
            json={"claim": "(x + y)^2 >= 4 * x * y", "target_language": "lean4"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["target_language"] == "lean4"
        assert "script" in data
        assert len(data["script"]) > 20

    def test_03_cluster_cache_status_endpoint(self, client):
        resp = client.get("/api/v1/cloud/cache/cluster-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "cache" in data

    def test_04_rate_limits_status_endpoint(self, client):
        resp = client.get("/api/v1/cloud/rate-limits/usr_enterprise_test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user_id"] == "usr_enterprise_test"
        assert "requests_per_minute_capacity" in data
