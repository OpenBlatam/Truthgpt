"""
🧪 Test Suite for Enhanced TruthGPT Cloud Platform Capabilities
Validates:
- Isabelle/HOL theorem exporter
- Transformer Attention invariants verification
- Quantization dynamic range and zero-point safety verification
- Optimizer convergence and spectral bounds
- Merkle non-membership exclusion proofs
- Multi-agent swarm debate and topologies
- Prometheus metrics formatting and /metrics endpoint
- FastAPI REST endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from truthgpt_cloud import (
    TruthGPTCloudClient,
    CloudTier,
    cloud_verifier,
    cloud_swarm,
    cloud_telemetry,
    format_prometheus_metrics
)
from truthgpt_cloud_server import app


class TestTruthGPTEnhancedSuite:

    def setup_method(self):
        self.client = TruthGPTCloudClient()
        self.api_client = TestClient(app)

    def test_01_isabelle_hol_exporter(self):
        """Verify that proof certificates export valid Isabelle/HOL formal code."""
        cert = self.client.verify_claim("x^2 + y^2 >= 2*x*y")
        assert cert is not None
        assert cert.status in ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"]

        # Test from certificate
        isabelle_code = cert.to_isabelle_script("am_gm_inequality")
        assert "theory TruthGPT_Verified_Theorem" in isabelle_code
        assert "imports Main Real" in isabelle_code
        assert "lemma am_gm_inequality:" in isabelle_code
        assert "shows" in isabelle_code
        assert "qed" in isabelle_code

        # Test from client
        isabelle_from_client = self.client.export_proof_to_isabelle(cert, "am_gm_inequality")
        assert "theory TruthGPT_Verified_Theory" in isabelle_from_client
        assert "lemma am_gm_inequality:" in isabelle_from_client

    def test_02_attention_invariants_verification(self):
        """Verify Transformer attention invariants (FlashAttention-3 / GQA / MHA)."""
        res = self.client.verify_attention_invariants(
            query_shape=[8, 2048, 4096],
            key_shape=[8, 2048, 4096],
            value_shape=[8, 2048, 4096],
            num_heads_q=32,
            num_heads_kv=8,
            head_dim=128,
            is_causal=True,
            architecture_type="FlashAttention-3"
        )
        assert res["success"] is True
        assert res["is_valid"] is True
        assert res["merkle_root"].startswith("0x")
        assert len(res["invariants_verified"]) >= 4

        # Test GQA invalid heads division
        res_invalid = self.client.verify_attention_invariants(
            query_shape=[8, 2048, 4096],
            key_shape=[8, 2048, 4096],
            value_shape=[8, 2048, 4096],
            num_heads_q=32,
            num_heads_kv=5,  # 32 % 5 != 0
            head_dim=128,
            is_causal=True
        )
        assert res_invalid["is_valid"] is False
        assert len(res_invalid["violations"]) > 0

    def test_03_quantization_safety_verification(self):
        """Verify FP8 / INT8 / BitNet quantization scale and clipping bounds."""
        res_int8 = self.client.verify_quantization_safety(
            min_val=-3.5,
            max_val=3.5,
            quant_format="INT8",
            symmetric=True
        )
        assert res_int8["success"] is True
        assert res_int8["is_valid"] is True
        assert res_int8["scale_factor"] > 0
        assert res_int8["merkle_root"].startswith("0x")

        # Test FP8 E4M3
        res_fp8 = self.client.verify_quantization_safety(
            min_val=-12.0,
            max_val=12.0,
            quant_format="FP8_E4M3",
            symmetric=True
        )
        assert res_fp8["success"] is True
        assert res_fp8["is_valid"] is True

        # Test BitNet b1.58
        res_bitnet = self.client.verify_quantization_safety(
            min_val=-1.0,
            max_val=1.0,
            quant_format="BITNET",
            symmetric=True
        )
        assert res_bitnet["success"] is True
        assert res_bitnet["is_valid"] is True

    def test_04_optimizer_convergence_verification(self):
        """Verify convergence guarantees and spectral norm invariants for optimizers."""
        res_adamw = self.client.verify_optimizer_convergence(
            optimizer_name="AdamW",
            learning_rate=1e-4,
            beta1=0.9,
            beta2=0.999,
            weight_decay=0.01,
            eps=1e-8
        )
        assert res_adamw["success"] is True
        assert res_adamw["is_valid"] is True
        assert res_adamw["merkle_root"].startswith("0x")

        # Test Muon Newton-Schulz optimizer
        res_muon = self.client.verify_optimizer_convergence(
            optimizer_name="Muon",
            learning_rate=0.02,
            beta1=0.95,
            beta2=0.999
        )
        assert res_muon["success"] is True
        assert res_muon["is_valid"] is True

        # Test unstable learning rate violation
        res_unstable = self.client.verify_optimizer_convergence(
            optimizer_name="SGD",
            learning_rate=50.0  # Excessive
        )
        assert res_unstable["is_valid"] is False

    def test_05_merkle_exclusion_proof(self):
        """Verify cryptographic non-membership exclusion in Merkle trees."""
        leaves = [
            "claim:x >= 0 -> x + 1 > 0",
            "status:PROVEN_VALID",
            "tier:ultra",
            "engine:Z3"
        ]
        res = self.client.verify_merkle_exclusion(
            tree_leaves=leaves,
            target_claim="claim:x < 0 -> false"  # Absent
        )
        assert res["verified_exclusion"] is True
        assert res["target_leaf_hash"] is not None
        assert res["root_hash"].startswith("0x")

    def test_06_prometheus_metrics_and_endpoints(self):
        """Verify Prometheus metrics line formatting and server endpoint."""
        metrics = cloud_telemetry.get_cluster_metrics()
        prom_text = format_prometheus_metrics(metrics)
        assert "truthgpt_cloud_uptime_seconds" in prom_text
        assert "truthgpt_cloud_inferences_total" in prom_text
        assert "truthgpt_cloud_soundness_percent" in prom_text

        # Test /metrics HTTP endpoint
        response = self.api_client.get("/metrics")
        assert response.status_code == 200
        assert "truthgpt_cloud_uptime_seconds" in response.text

    def test_07_fastapi_enhanced_endpoints(self):
        """Verify enhanced FastAPI endpoints."""
        # 1. Test Attention verification endpoint
        attn_resp = self.api_client.post(
            "/api/v1/cloud/formal/verify/attention",
            json={
                "query_shape": [4, 512, 1024],
                "key_shape": [4, 512, 1024],
                "value_shape": [4, 512, 1024],
                "num_heads_q": 16,
                "num_heads_kv": 4,
                "head_dim": 64
            }
        )
        assert attn_resp.status_code == 200
        assert attn_resp.json()["is_valid"] is True

        # 2. Test Quantization verification endpoint
        quant_resp = self.api_client.post(
            "/api/v1/cloud/formal/verify/quantization",
            json={
                "min_val": -2.0,
                "max_val": 2.0,
                "quant_format": "INT8"
            }
        )
        assert quant_resp.status_code == 200
        assert quant_resp.json()["is_valid"] is True

        # 3. Test Optimizer verification endpoint
        opt_resp = self.api_client.post(
            "/api/v1/cloud/formal/verify/optimizer",
            json={
                "optimizer_name": "AdamW",
                "learning_rate": 0.001
            }
        )
        assert opt_resp.status_code == 200
        assert opt_resp.json()["is_valid"] is True

        # 4. Test Merkle Exclusion endpoint
        merkle_resp = self.api_client.post(
            "/api/v1/cloud/formal/verify/merkle-exclusion",
            json={
                "tree_leaves": ["leaf_A", "leaf_B", "leaf_C"],
                "target_claim": "leaf_D"
            }
        )
        assert merkle_resp.status_code == 200
        assert merkle_resp.json()["verified_exclusion"] is True

        # 5. Test Isabelle certificate export endpoint
        cert = self.client.verify_claim("a * b == b * a")
        isabelle_resp = self.api_client.get(f"/api/v1/cloud/formal/certificate/{cert.certificate_id}/isabelle")
        assert isabelle_resp.status_code == 200
        assert "theory TruthGPT_Verified_Theory" in isabelle_resp.text
