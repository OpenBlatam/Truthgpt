"""
🧪 Unit Tests - TruthGPT Cloud Production Library Enhancements
Validates integration of:
1. Cryptography (Ed25519 asymmetric signatures, constant-time bytes_eq)
2. xxHash (Sub-microsecond hashing)
3. Zstandard (Lossless high-ratio payload compression)
4. Prometheus Client (CollectorRegistry, standard exposition /metrics)
5. HTTPX (Sync/Async connection pooling, context managers)
6. Pydantic v2 (Canonical schemas, data validation, domain conversions)
"""

import pytest
import json
from pydantic import ValidationError
from fastapi.testclient import TestClient

from truthgpt_cloud import (
    ProofCertificate,
    generate_ed25519_keypair,
    proof_cache,
    cloud_telemetry,
    cloud_security,
    TruthGPTCloudClient,
    get_prometheus_registry,
    generate_prometheus_metrics,
    ProofCertificateSchema,
    TierConfigSchema,
    AlertRuleSchema,
    get_tier_config,
    CloudTier,
)
from truthgpt_cloud_server import app


class TestCryptographyEnhancements:
    """Test asymmetric Ed25519 signatures and constant-time security hardening."""

    def test_01_ed25519_keypair_generation(self):
        priv_hex, pub_hex = generate_ed25519_keypair()
        assert isinstance(priv_hex, str)
        assert isinstance(pub_hex, str)
        assert len(priv_hex) == 64  # 32 bytes in hex
        assert len(pub_hex) == 64   # 32 bytes in hex
        assert priv_hex != pub_hex

    def test_02_proof_certificate_asymmetric_signing_and_verification(self):
        priv_hex, pub_hex = generate_ed25519_keypair()
        cert = ProofCertificate(
            certificate_id="cert-crypto-test-01",
            theorem_or_claim="(x + y)^2 >= 4*x*y",
            status="PROVEN_VALID",
            confidence_score=1.0,
            solver_engine="z3_smt-4.16.0",
            verification_time_ms=12.5,
            proof_tree_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            proof_steps=["Step 1", "Step 2"],
            mathematical_invariants=["x >= 0", "y >= 0"],
        )

        assert cert.asymmetric_signature is None
        sig_hex = cert.sign_asymmetric(priv_hex)
        assert sig_hex is not None
        assert cert.asymmetric_signature == sig_hex
        assert cert.public_key_hex == pub_hex

        # Verification with embedded public key
        assert cert.verify_asymmetric_signature() is True

        # Verification with explicit public key
        assert cert.verify_asymmetric_signature(pub_hex) is True

        # Verification fails with wrong public key
        _, other_pub = generate_ed25519_keypair()
        assert cert.verify_asymmetric_signature(other_pub) is False

        # Verification fails if signature is tampered
        original_sig = cert.asymmetric_signature
        cert.asymmetric_signature = "00" * 64
        assert cert.verify_asymmetric_signature() is False
        cert.asymmetric_signature = original_sig

    def test_03_constant_time_session_token_validation(self):
        token = cloud_security.generate_session_token("usr_test_crypto", duration_seconds=300)
        assert token.startswith("sess_tgpt_")

        # Valid validation
        val = cloud_security.validate_session_token(token)
        assert val["is_valid"] is True
        assert val["user_id"] == "usr_test_crypto"

        # Tampered signature validation rejection
        parts = token.split(".")
        tampered_token = f"{parts[0]}.{parts[1][:-4]}abcd"
        tampered_val = cloud_security.validate_session_token(tampered_token)
        assert tampered_val["is_valid"] is False
        assert "Invalid token signature" in tampered_val["reason"]

    def test_04_ledger_block_ed25519_signing_and_verification(self):
        priv_hex, pub_hex = generate_ed25519_keypair()
        block = cloud_security.append_audit_block(
            event_type="SECURITY_AUDIT_CHECKPOINT",
            user_id="usr_admin",
            details={"checkpoint": "alpha_1"}
        )
        assert block.asymmetric_signature is None

        sig = cloud_security.sign_audit_block(block, priv_hex)
        assert sig is not None
        assert block.asymmetric_signature == sig
        assert block.public_key_hex == pub_hex

        # Verify authentic signature
        assert cloud_security.verify_audit_block(block) is True

        # Verify fails if public key differs
        _, other_pub = generate_ed25519_keypair()
        assert cloud_security.verify_audit_block(block, other_pub) is False


class TestXxhashAndZstandardEnhancements:
    """Test xxHash ultra-fast hashing and Zstandard binary compression in ProofCache."""

    def test_01_xxhash_fast_hashing(self):
        claim = "forall x in R: x^2 + 1 > 0"
        constraints = ["x != 0"]
        h1 = proof_cache.compute_fast_hash(claim, constraints)
        h2 = proof_cache.compute_fast_hash(claim, constraints)
        assert isinstance(h1, str)
        assert h1 == h2
        assert len(h1) == 16  # 64-bit hex is 16 chars

    def test_02_zstandard_compression_roundtrip(self):
        large_payload = {
            "certificate_id": "cert-big-data-12345",
            "proof_steps": [f"Lemma step {i}: x_{i} <= x_{i+1} + delta_{i}" for i in range(100)],
            "mathematical_invariants": [f"Invariant #{i}: sum(x) >= {i}" for i in range(50)],
            "ast_metadata": {"nodes": 450, "solver": "z3-smt-4.16.0", "tactics": ["simplify", "solve-eqs", "smt"]}
        }
        compressed = proof_cache.compress_data(large_payload)
        assert isinstance(compressed, bytes)
        raw_size = len(json.dumps(large_payload).encode("utf-8"))
        assert len(compressed) < raw_size  # Effective compression
        ratio = (1.0 - (len(compressed) / raw_size)) * 100
        assert ratio > 40.0  # Significant reduction

        # Decompress roundtrip
        decompressed = proof_cache.decompress_data(compressed, as_json=True)
        assert decompressed == large_payload

    def test_03_proof_cache_stats_metrics(self):
        stats = proof_cache.get_stats()
        assert "has_xxhash" in stats
        assert "has_zstandard" in stats
        assert stats["has_xxhash"] is True
        assert stats["has_zstandard"] is True
        assert "total_bytes_compressed" in stats
        assert "total_bytes_saved" in stats


class TestPrometheusClientObservability:
    """Test Prometheus CollectorRegistry and metrics generation."""

    def test_01_prometheus_registry_and_metrics_generation(self):
        reg = get_prometheus_registry()
        assert reg is not None

        cloud_telemetry.record_inference(latency_ms=25.4, tokens=120, tier="pro")
        cloud_telemetry.record_verification(latency_ms=8.2, status="PROVEN_VALID")
        cloud_telemetry.record_swarm()

        raw_bytes = generate_prometheus_metrics()
        assert isinstance(raw_bytes, bytes)
        decoded = raw_bytes.decode("utf-8")
        assert "truthgpt_cloud_inferences_total" in decoded
        assert "truthgpt_cloud_verifications_total" in decoded
        assert "truthgpt_cloud_swarms_total" in decoded

    def test_02_prometheus_metrics_endpoint(self):
        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        body = resp.text
        assert "truthgpt_cloud_uptime_seconds" in body
        assert "truthgpt_cloud_inferences_total" in body


class TestHttpxClientIntegration:
    """Test HTTPX integration in TruthGPTCloudClient."""

    def test_01_httpx_sync_client_and_context_manager(self):
        client = TruthGPTCloudClient(api_key="tgpt_cloud_live_demo", base_url="http://localhost:8080")
        assert client._is_remote is True
        assert client.base_url == "http://localhost:8080"

        http_c = client.get_http_client()
        assert http_c is not None
        assert hasattr(http_c, "get")

        # Sync context manager
        with client as c:
            assert c._http_client is not None
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_02_httpx_async_client_and_context_manager(self):
        client = TruthGPTCloudClient(api_key="tgpt_cloud_live_demo", base_url="http://localhost:8080")
        async_http_c = await client.get_async_http_client()
        assert async_http_c is not None
        assert hasattr(async_http_c, "get")

        # Async context manager
        async with client as c:
            assert c._async_http_client is not None
        assert client._async_http_client is None

    def test_03_local_in_process_fallback(self):
        # Client without base_url remains purely local
        client = TruthGPTCloudClient(api_key="tgpt_cloud_live_demo")
        assert client._is_remote is False
        assert client.is_authenticated is True
        stats = client.get_stats()
        assert "tier" in stats
        assert "cache" in stats


class TestPydanticV2Schemas:
    """Test Pydantic v2 schemas validation, serialization, and domain conversions."""

    def test_01_proof_certificate_schema_roundtrip(self):
        data = {
            "certificate_id": "cert-pydantic-001",
            "theorem_or_claim": "x >= 0 -> x + 1 > 0",
            "status": "PROVEN_VALID",
            "confidence_score": 0.9999,
            "solver_engine": "z3_smt",
            "verification_time_ms": 15.2,
            "proof_tree_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "proof_steps": ["Step 1", "Step 2"],
            "mathematical_invariants": ["x >= 0"],
        }
        schema = ProofCertificateSchema.model_validate(data)
        assert schema.certificate_id == "cert-pydantic-001"
        assert schema.confidence_score == 0.9999

        # Convert to domain ProofCertificate
        domain_cert = schema.to_domain()
        assert isinstance(domain_cert, ProofCertificate)
        assert domain_cert.certificate_id == "cert-pydantic-001"

        # Convert back from domain object
        schema2 = ProofCertificateSchema.from_domain(domain_cert)
        assert schema2.certificate_id == schema.certificate_id

    def test_02_proof_certificate_schema_validation_error(self):
        with pytest.raises(ValidationError):
            # confidence_score > 1.0 must fail validation
            ProofCertificateSchema(
                certificate_id="cert-invalid",
                theorem_or_claim="1 == 1",
                status="PROVEN_VALID",
                confidence_score=1.5,
                proof_tree_hash="hash123",
            )

    def test_03_tier_config_schema(self):
        tier_cfg = get_tier_config(CloudTier.PRO)
        schema = TierConfigSchema.from_domain(tier_cfg)
        assert schema.tier == "pro"
        assert schema.daily_token_quota > 0
        assert schema.monthly_price_usd >= 0.0

    def test_04_alert_rule_schema(self):
        rule_data = {
            "name": "high_p99_latency",
            "metric_key": "p99_latency_ms",
            "threshold": 500.0,
            "comparison": "gte",
            "is_active": True,
            "cooldown_seconds": 30.0,
        }
        schema = AlertRuleSchema.model_validate(rule_data)
        assert schema.comparison == "gte"

        # Invalid comparison operator must fail
        rule_data["comparison"] = "invalid_op"
        with pytest.raises(ValidationError):
            AlertRuleSchema.model_validate(rule_data)
