"""
🧪 TruthGPT Cloud - Advanced Library Enhancements Test Suite
Validates integrations for:
- tiktoken (exact BPE token counting)
- structlog (enterprise structured cloud logging)
- simsimd (hardware-accelerated vector similarity search)
- rich (high-fidelity CLI terminal interfaces)
"""

import logging
from unittest.mock import patch

from truthgpt_cloud.routing import (
    count_tokens,
    _HAS_TIKTOKEN,
    CloudIntelligenceRouter,
)
from truthgpt_cloud.telemetry.structured_logging import (
    get_logger,
    configure_logging,
    bind_context,
    unbind_context,
    _HAS_STRUCTLOG,
    _FallbackLogger,
)
from truthgpt_cloud.cache.proof_cache import (
    proof_cache,
    _compute_cosine_similarity,
    _HAS_SIMSIMD,
)
import truthgpt_cloud_cli


class TestTiktokenIntegration:
    """Validate tiktoken BPE token counting engine."""

    def test_01_tiktoken_is_active(self):
        assert _HAS_TIKTOKEN is True, "tiktoken should be installed and detected in environment"

    def test_02_count_tokens_exact_matches(self):
        # Empty string
        assert count_tokens("") == 0
        assert count_tokens(None) == 0

        # Exact BPE tokens
        text = "TruthGPT Cloud provides formal verification with Z3 SMT solvers."
        tokens = count_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0
        # Compare with direct tiktoken encode
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        assert tokens == len(enc.encode(text))

    def test_03_count_tokens_fallback_heuristic(self):
        with patch("truthgpt_cloud.routing.router._HAS_TIKTOKEN", False):
            with patch("truthgpt_cloud.routing.router._TIKTOKEN_ENCODER", None):
                text = "one two three four five"
                fallback_tokens = count_tokens(text)
                # Heuristic: 5 * 1.4 = 7
                assert fallback_tokens == 7

    def test_04_router_uses_count_tokens(self):
        router = CloudIntelligenceRouter()
        prompt = "∀x ∈ ℝ: x^2 ≥ 0"
        validated = router._validate_prompt(prompt, max_tokens=1000)
        assert validated == prompt


class TestStructlogIntegration:
    """Validate structlog structured logging and observability."""

    def test_01_has_structlog_active(self):
        assert _HAS_STRUCTLOG is True, "structlog should be installed and detected"

    def test_02_get_logger_and_logging_levels(self):
        logger = get_logger("truthgpt.test")
        assert logger is not None
        # Should execute without errors
        logger.info("inference_started", model="deepseek-r1", user_id="usr_test_123")
        logger.debug("cache_lookup", key="0xabc123")
        logger.warning("quota_approaching", current=85000, limit=100000)

    def test_03_bind_and_unbind_context(self):
        bind_context(request_id="req_998877", tier="ultra")
        logger = get_logger("truthgpt.ctx_test")
        logger.info("testing_context_binding")
        unbind_context("request_id", "tier")

    def test_04_configure_logging_json_and_console(self):
        # Test JSON configuration
        configure_logging(json_format=True, log_level="DEBUG")
        logger = get_logger("truthgpt.json_test")
        logger.info("json_log_event", status="OK")

        # Test Console configuration
        configure_logging(json_format=False, log_level="INFO")
        logger.info("console_log_event", status="READY")

    def test_05_fallback_logger(self):
        std_logger = logging.getLogger("fallback_test")
        fb = _FallbackLogger(std_logger)
        bound = fb.bind(session="s_123")
        assert bound._context["session"] == "s_123"
        unbound = bound.unbind("session")
        assert "session" not in unbound._context
        # Test calls
        bound.info("fallback_info_event", code=200)
        bound.warning("fallback_warning_event", retry=True)


class TestSimsimdIntegration:
    """Validate SimSIMD hardware-accelerated vector similarity."""

    def test_01_has_simsimd_active(self):
        assert _HAS_SIMSIMD is True, "simsimd should be installed and detected"

    def test_02_compute_cosine_similarity(self):
        # Parallel vectors: similarity ~ 1.0
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        sim_parallel = _compute_cosine_similarity(v1, v2)
        assert abs(sim_parallel - 1.0) < 1e-4

        # Orthogonal vectors: similarity ~ 0.0
        v3 = [0.0, 1.0, 0.0]
        sim_ortho = _compute_cosine_similarity(v1, v3)
        assert abs(sim_ortho) < 1e-4

        # Opposite vectors: similarity ~ -1.0
        v4 = [-1.0, 0.0, 0.0]
        sim_opp = _compute_cosine_similarity(v1, v4)
        assert abs(sim_opp - (-1.0)) < 1e-4

    def test_03_find_similar_proofs_in_cache(self):
        # Store proofs with simulated domain embeddings
        # Vector dim = 4
        # Algebra cluster: [1.0, 0.8, 0.0, 0.0]
        # Geometry cluster: [0.0, 0.0, 1.0, 0.9]
        proof_cache.store_proof(
            claim="x^2 >= 0 for all real x",
            certificate_data={"status": "PROVEN", "domain": "algebra"},
            embedding=[1.0, 0.85, 0.05, 0.0],
            ttl_seconds=600,
        )
        proof_cache.store_proof(
            claim="a + b = b + a",
            certificate_data={"status": "PROVEN", "domain": "algebra"},
            embedding=[0.95, 0.9, 0.0, 0.0],
            ttl_seconds=600,
        )
        proof_cache.store_proof(
            claim="Pythagorean theorem a^2 + b^2 = c^2",
            certificate_data={"status": "PROVEN", "domain": "geometry"},
            embedding=[0.0, 0.05, 0.95, 0.9],
            ttl_seconds=600,
        )

        # Query with an algebra-oriented embedding
        query_vector = [1.0, 0.8, 0.0, 0.0]
        results = proof_cache.find_similar_proofs(query_vector, top_k=2, min_similarity=0.7)

        assert len(results) >= 2
        top_entry, top_score = results[0]
        assert top_score > 0.9
        assert top_entry.certificate_data["domain"] == "algebra"

    def test_04_cache_stats_reports_simsimd(self):
        stats = proof_cache.get_stats()
        assert "has_simsimd" in stats
        assert stats["has_simsimd"] is True


class TestRichCliIntegration:
    """Validate Rich console enhancement in CLI."""

    def test_01_has_rich_active(self):
        assert truthgpt_cloud_cli._HAS_RICH is True, "rich should be active in CLI module"

    def test_02_banner_and_user_status(self):
        # Execution of print_banner should not raise
        truthgpt_cloud_cli.print_banner()

        dummy_status = {
            "name": "Dr. Alan Turing",
            "email": "turing@truthgpt.ai",
            "tier_name": "TruthGPT Ultra",
            "tier_badge": "ULTRA-QUANTUM",
            "metrics": {
                "tokens_consumed_today": 125000,
                "daily_token_limit": 1000000,
                "percent_quota_used": 12.5,
            },
            "features": {
                "smt_verification_depth": 3,
                "latency_tier": "sub-10ms",
            }
        }
        truthgpt_cloud_cli.print_user_status(dummy_status)

    def test_03_subscription_matrix(self):
        tiers = [
            {
                "name": "Free",
                "badge": "LITE",
                "price_monthly_usd": 0,
                "daily_token_limit": 50000,
                "requests_per_minute": 20,
                "max_swarm_agents": 1,
                "smt_verification_level": "Level 1",
            },
            {
                "name": "Pro",
                "badge": "PRO",
                "price_monthly_usd": 49,
                "daily_token_limit": 500000,
                "requests_per_minute": 120,
                "max_swarm_agents": 4,
                "smt_verification_level": "Level 2",
            }
        ]
        truthgpt_cloud_cli.print_subscription_matrix(tiers)
