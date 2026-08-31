"""
🧪 Test Suite for TruthGPT Cloud Ecosystem
Tests tiers, subscription management, Z3 formal verifier, multi-agent swarm, and API routes.
"""

import sys
import os
import pytest
import asyncio
from pathlib import Path

# Ensure paths
_current = Path(__file__).resolve().parent.parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from truthgpt_cloud import (
    CloudTier,
    TierConfig,
    get_tier_config,
    get_all_tiers,
    SubscriptionManager,
    subscription_manager,
    CloudFormalVerifier,
    cloud_verifier,
    CloudSwarmOrchestrator,
    cloud_swarm,
    CloudIntelligenceRouter,
    cloud_router,
    TruthGPTCloudClient
)


def test_tier_matrix():
    """Verify tier configurations and properties."""
    tiers = get_all_tiers()
    assert len(tiers) == 4
    tier_ids = [t["tier_id"] for t in tiers]
    assert "free" in tier_ids
    assert "pro" in tier_ids
    assert "ultra" in tier_ids
    assert "enterprise" in tier_ids

    pro_cfg = get_tier_config(CloudTier.PRO)
    assert pro_cfg.price_monthly_usd == 19.99
    assert pro_cfg.smt_z3_verification_depth == 2
    assert pro_cfg.daily_token_limit == 2_000_000
    assert pro_cfg.proof_certificate_generation is True

    ultra_cfg = get_tier_config(CloudTier.ULTRA)
    assert ultra_cfg.price_monthly_usd == 99.99
    assert ultra_cfg.max_swarm_agents == 20
    assert ultra_cfg.context_window_tokens == 2_000_000


def test_subscription_manager():
    """Test user registration, upgrade, invoices and API keys."""
    sm = SubscriptionManager(storage_path=None)  # Uses default test instance
    user = sm.register_user(email="test_user@truthgpt.ai", name="Test User", tier=CloudTier.FREE)
    assert user.user_id.startswith("usr_")
    assert user.tier == CloudTier.FREE
    assert len(user.api_keys) >= 1

    # Upgrade to Pro
    upgrade_res = sm.upgrade_subscription(
        user_id=user.user_id,
        target_tier=CloudTier.PRO,
        billing_cycle="yearly",
        payment_method="stripe_card"
    )
    assert upgrade_res["success"] is True
    assert upgrade_res["new_tier"] == "pro"
    assert len(user.invoices) >= 1

    # Summary
    summary = sm.get_user_status_summary(user.user_id)
    assert summary["tier"] == "pro"
    assert summary["metrics"]["tokens_consumed_today"] == 0

    # Quota check
    sm.check_and_record_quota(user.user_id, estimated_tokens=1000)
    summary_after = sm.get_user_status_summary(user.user_id)
    assert summary_after["metrics"]["tokens_consumed_today"] == 1000


def test_cloud_formal_verifier():
    """Test Z3/SymPy formal verification and certificate generation."""
    verifier = CloudFormalVerifier()
    cert = verifier.verify_expression(
        claim_text="∀x, y ∈ ℝ⁺: x + y ≥ 0",
        tier_depth=2
    )
    assert cert.certificate_id.startswith("proof_cert_")
    assert cert.status in ["PROVEN_SAT", "PROVEN_VALID", "VERIFIED_SYMBOLIC"]
    assert cert.confidence_score >= 0.95
    assert cert.proof_tree_hash.startswith("0x")
    assert len(cert.mathematical_invariants) >= 1


@pytest.mark.asyncio
async def test_cloud_swarm_orchestrator():
    """Test multi-agent swarm execution."""
    swarm = CloudSwarmOrchestrator()
    trace = await swarm.execute_swarm_session(
        prompt="Design optimal tensor parallel strategy for LLM training",
        max_agents=5
    )
    assert trace.session_id.startswith("swarm_sess_")
    assert len(trace.agents_involved) == 5
    assert "consenso" in trace.consensus_summary.lower()


@pytest.mark.asyncio
async def test_cloud_router_inference():
    """Test tier-aware inference routing."""
    router = CloudIntelligenceRouter()
    
    # Pro Tier inference
    user_pro = subscription_manager.get_user("usr_pro_sample")
    uid = user_pro.user_id if user_pro else "usr_default_demo"
    
    response = await router.route_inference(
        prompt="Solve non-linear convex optimization",
        user_id=uid,
        enable_formal_verification=True
    )
    assert response.response_id.startswith("resp_tgpt_")
    assert response.verification_passed is True
    assert response.proof_certificate is not None
    assert response.tokens_consumed > 0


def test_truthgpt_cloud_client_sdk():
    """Test Python Client SDK interface."""
    client = TruthGPTCloudClient()
    status = client.get_subscription_status()
    assert "tier" in status
    assert "metrics" in status

    # Verify claim
    cert = client.verify_claim("∀a,b: a^2 - b^2 = (a-b)(a+b)")
    assert cert.proof_tree_hash is not None


def test_fastapi_server_endpoints():
    """Test TruthGPT Cloud FastAPI endpoints using TestClient."""
    from fastapi.testclient import TestClient
    from truthgpt_cloud_server import app

    client = TestClient(app)
    
    # Health
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    # Tiers
    r = client.get("/api/v1/cloud/tiers")
    assert r.status_code == 200
    assert len(r.json()["tiers"]) == 4

    # Subscription Me
    r = client.get("/api/v1/cloud/subscription/me?user_id=usr_pro_sample")
    assert r.status_code == 200
    assert "subscription" in r.json()

    # Formal Verify
    r = client.post("/api/v1/cloud/formal/verify", json={"claim": "2 + 2 = 4"})
    assert r.status_code == 200
    assert "certificate" in r.json()

    # Papers Hub
    r = client.get("/api/v1/cloud/papers/hub")
    assert r.status_code == 200
    assert r.json()["total_papers"] >= 3
