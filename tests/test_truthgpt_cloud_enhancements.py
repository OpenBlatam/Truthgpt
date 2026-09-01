"""
🧪 TruthGPT Cloud - Comprehensive Enhancements Test Suite
Validates formal verification, multi-agent reasoning DAGs, semantic proof caching,
telemetry diagnostics, security session tokens, billing promo codes, and SOTA paper citations.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from truthgpt_cloud import (
    TruthGPTCloudClient,
    CloudTier,
    cloud_verifier,
    cloud_swarm,
    proof_cache,
    cloud_telemetry,
    cloud_security,
    subscription_manager,
    ProofCertificate,
)
from truthgpt_cloud.papers.registry import (
    search_papers,
    export_bibtex,
    export_apa,
    export_ieee,
)
from truthgpt_cloud_server import app


class TestTruthGPTCloudEnhancements:

    def setup_method(self):
        self.client = TruthGPTCloudClient(tier=CloudTier.PRO)

    def test_01_isabelle_and_mermaid_proof_exports(self):
        cert = self.client.verify_expression("x^2 + y^2 >= 2*x*y")
        assert cert.status in ["PROVEN_VALID", "PROVEN_SAT", "VERIFIED_SYMBOLIC"]
        
        # Isabelle/HOL export
        isabelle_code = cert.to_isabelle_script()
        assert "theory TruthGPT_Verified_Theorem" in isabelle_code
        assert "lemma" in isabelle_code
        assert "qed" in isabelle_code

        # SMT-LIB2 export helper on verifier
        smt2_code = cloud_verifier.export_to_smt2(cert)
        assert "(set-logic QF_NRA)" in smt2_code
        assert "(check-sat)" in smt2_code

        # Mermaid DAG
        mermaid_code = cert.to_mermaid_dag()
        assert "graph TD" in mermaid_code
        assert "Root" in mermaid_code
        assert "Merkle" in mermaid_code

        # Markdown Report
        md_report = cert.to_markdown_report()
        assert "Certificado de Verificación Formal TruthGPT Cloud" in md_report
        assert cert.certificate_id in md_report

    def test_02_matrix_and_linear_algebra_invariants(self):
        # 2x2 Symmetric positive-definite diagonally dominant matrix
        matrix_pd = [
            [4.0, 1.0],
            [1.0, 3.0]
        ]
        res = self.client.verify_matrix(matrix_pd, matrix_name="Covariance_Matrix")
        assert res["success"] is True
        assert res["is_square"] is True
        assert res["is_symmetric"] is True
        assert res["is_diagonally_dominant"] is True
        assert res["trace"] == 7.0
        assert res["is_positive_definite"] is True
        assert res["spectral_radius_upper_bound"] > 0
        assert "proof_certificate" in res
        assert res["proof_certificate"]["status"] == "MATRIX_INVARIANTS_PROVEN"

    def test_03_ode_and_lyapunov_stability(self):
        # Stable continuous system matrix (Hurwitz stable)
        stable_ode = [
            [-3.0, 1.0],
            [1.0, -4.0]
        ]
        res = self.client.verify_ode(stable_ode, system_name="Gradient_Flow_ODE")
        assert res["success"] is True
        assert res["is_continuous_hurwitz"] is True
        assert res["stable"] is True
        assert "Hurwitz Asymptotic Stability Criterion" in res["invariants_verified"][1]

    def test_04_hoare_loop_invariant_verification(self):
        res = self.client.verify_loop(
            loop_condition="i < n",
            invariant_claim="0 <= i <= n and sum == i * (i + 1) / 2",
            loop_body_effect="sum = sum + i; i = i + 1"
        )
        assert res["success"] is True
        assert res["is_valid"] is True
        assert res["proof_certificate"]["status"] == "HOARE_LOOP_VERIFIED"
        assert res["merkle_root"].startswith("0x")

    def test_05_swarm_mermaid_graph_and_reasoning_dag(self):
        trace = self.client.run_swarm(
            prompt="Probar convergencia asintótica de SGD con momentum",
            max_agents=4
        )
        assert trace.session_id.startswith("swarm_sess_")
        
        # Mermaid graph
        mermaid = trace.to_mermaid_graph()
        assert "graph TD" in mermaid
        assert "Prompt" in mermaid
        assert "Consensus" in mermaid

        # Reasoning DAG
        dag = trace.to_reasoning_dag()
        assert dag["nodes_count"] >= 5
        assert dag["edges_count"] >= 8
        assert dag["nodes"][0]["type"] == "input"
        assert dag["nodes"][-1]["type"] == "output"

    def test_06_commutative_proof_cache_and_snapshots(self):
        proof_cache.clear()
        
        # Store claim A == B
        cert = cloud_verifier.verify_expression("a + b == c")
        proof_cache.store_proof("x + y == z", cert.to_dict())

        # Retrieve with commutative order z == x + y (should HIT cache due to canonical sort)
        hit_cert = proof_cache.get_proof("z == x + y")
        assert hit_cert is not None
        assert hit_cert["certificate_id"] == cert.certificate_id

        # Dump and load cache snapshot
        claims = proof_cache.list_cached_claims()
        assert len(claims) >= 1
        
        snapshot = proof_cache.dump_cache()
        assert len(snapshot) >= 1

        proof_cache.clear()
        assert len(proof_cache.list_cached_claims()) == 0

        loaded = proof_cache.load_cache(snapshot)
        assert loaded >= 1
        assert len(proof_cache.list_cached_claims()) >= 1

    def test_07_telemetry_health_and_opentelemetry_spans(self):
        cloud_telemetry.record_audit_event("kernel_compile", "usr_test", {"kernel": "mla_attention"})
        
        # Health check
        health = cloud_telemetry.get_health_status()
        assert health["status"] in ["HEALTHY", "DEGRADED"]
        assert "components" in health
        assert "cluster_metrics" in health

        # OpenTelemetry Spans
        spans = cloud_telemetry.to_opentelemetry_spans(limit=10)
        assert len(spans) >= 1
        assert spans[-1]["name"] == "truthgpt.cloud.kernel_compile"
        assert spans[-1]["kind"] == "SPAN_KIND_SERVER"
        assert "attributes" in spans[-1]

    def test_08_security_session_tokens_and_ip_validation(self):
        user_id = "usr_token_test"
        token = cloud_security.generate_session_token(user_id, duration_seconds=1800, scopes=["inference", "verify"])
        assert token.startswith("sess_tgpt_")

        validation = cloud_security.validate_session_token(token)
        assert validation["is_valid"] is True
        assert validation["user_id"] == user_id
        assert "inference" in validation["scopes"]

        # Invalid token signature check
        bad_token = token[:-4] + "ffff"
        bad_validation = cloud_security.validate_session_token(bad_token)
        assert bad_validation["is_valid"] is False

    def test_09_billing_promo_codes_and_text_receipts(self):
        user = subscription_manager.register_user(
            email="promouser@truthgpt.ai",
            name="Promo Tester",
            tier=CloudTier.FREE
        )
        
        # Upgrade with 20% discount code TRUTH2026
        res = subscription_manager.upgrade_subscription(
            user_id=user.user_id,
            target_tier=CloudTier.PRO,
            billing_cycle="monthly",
            promo_code="TRUTH2026"
        )
        assert res["success"] is True
        assert res["invoice"]["promo_code"] == "TRUTH2026"
        assert res["invoice"]["discount_applied_usd"] > 0
        assert res["invoice"]["amount_usd"] < 19.99

        # Text Receipt
        inv = user.invoices[0]
        receipt_text = inv.to_text_receipt()
        assert "TRUTHGPT CLOUD - OFFICIAL INVOICE RECEIPT" in receipt_text
        assert "TRUTH2026" in receipt_text
        assert str(inv.invoice_id) in receipt_text

    def test_10_paper_search_and_citations(self):
        # Search
        mla_papers = search_papers(query="latent attention")
        assert len(mla_papers) >= 1
        assert "mla" in mla_papers[0].paper_id or "deepseek" in mla_papers[0].paper_id

        # Citations
        paper_id = "arxiv_2026_deepseek_mla"
        bib = export_bibtex(paper_id)
        assert "@article{" in bib
        assert "DeepSeek" in bib

        apa = export_apa(paper_id)
        assert "(2026)" in apa

        ieee = export_ieee(paper_id)
        assert "[1]" in ieee

    def test_11_client_context_managers_and_helpers(self):
        # Synchronous context manager
        with TruthGPTCloudClient(tier=CloudTier.PRO) as cli:
            h = cli.get_health_status()
            assert h["status"] in ["HEALTHY", "DEGRADED"]
            cite = cli.export_paper_citation("arxiv_2026_deepseek_mla", format_type="bibtex")
            assert "@article{" in cite

        # Async context manager
        async def run_async_test():
            async with TruthGPTCloudClient(tier=CloudTier.PRO) as cli:
                res = await cli.ask_async("x >= 0 implies x + 1 > 0")
                assert res.verification_passed is True

        asyncio.run(run_async_test())

    def test_12_fastapi_server_new_endpoints(self):
        test_client = TestClient(app)

        # Health endpoint
        resp = test_client.get("/api/v1/cloud/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "components" in data

        # Matrix verification endpoint
        matrix_payload = {
            "matrix": [[5.0, 0.5], [0.5, 3.0]],
            "matrix_name": "Hessian_Matrix"
        }
        resp = test_client.post("/api/v1/cloud/formal/verify/matrix", json=matrix_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_symmetric"] is True

        # ODE verification endpoint
        ode_payload = {
            "system_matrix": [[-2.0, 0.5], [0.5, -3.0]],
            "system_name": "Continuous_Filter_ODE"
        }
        resp = test_client.post("/api/v1/cloud/formal/verify/ode", json=ode_payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Loop verification endpoint
        loop_payload = {
            "loop_condition": "k < 100",
            "invariant_claim": "0 <= k <= 100",
            "loop_body_effect": "k = k + 1"
        }
        resp = test_client.post("/api/v1/cloud/formal/verify/loop", json=loop_payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Paper search endpoint
        resp = test_client.get("/api/v1/cloud/papers/search?query=flash")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

        # Paper citation endpoint
        resp = test_client.get("/api/v1/cloud/papers/arxiv_2026_flash_attn_3/citation?format=bibtex")
        assert resp.status_code == 200
        assert "@article{" in resp.text
