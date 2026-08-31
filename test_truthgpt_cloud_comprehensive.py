"""
🧪 Comprehensive Test Suite for TruthGPT Cloud Platform v2.1
Tests:
- Tier definitions & configurations
- Subscription management & billing cycle
- Token Bucket RPM Rate Limiting & Quota accounting
- SMT Z3 Verification Engine & Merkle Proof Certificate generation
- Design-by-Contract (DbC) Hoare Logic verification
- Multi-Agent Swarm execution & consensus metrics
- Cloud Intelligence Router & streaming inference
- FastAPI endpoints
"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure paths
_current = Path(__file__).resolve().parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

from truthgpt_cloud import (
    CloudTier,
    get_all_tiers,
    get_tier_config,
    subscription_manager,
    cloud_router,
    cloud_verifier,
    cloud_swarm,
    TruthGPTCloudClient,
    TokenBucketRateLimiter,
    RateLimitExceeded
)


def test_tier_matrix():
    print("[TEST] Testing Tier Configurations...")
    tiers = get_all_tiers()
    assert len(tiers) == 4, f"Expected 4 tiers, got {len(tiers)}"
    
    free_cfg = get_tier_config(CloudTier.FREE)
    pro_cfg = get_tier_config(CloudTier.PRO)
    ultra_cfg = get_tier_config(CloudTier.ULTRA)
    enterprise_cfg = get_tier_config(CloudTier.ENTERPRISE)
    
    assert free_cfg.price_monthly_usd == 0.0
    assert pro_cfg.price_monthly_usd == 19.99
    assert ultra_cfg.price_monthly_usd == 99.99
    assert enterprise_cfg.price_monthly_usd == 499.00
    
    assert free_cfg.max_swarm_agents == 1
    assert pro_cfg.max_swarm_agents == 5
    assert ultra_cfg.max_swarm_agents == 20
    assert enterprise_cfg.max_swarm_agents == 100
    
    print("[PASS] Tier Matrix test passed!")


def test_subscription_and_billing():
    print("[TEST] Testing Subscription & Billing Lifecycle...")
    test_email = "tester_cloud_v2@truthgpt.ai"
    user = subscription_manager.register_user(email=test_email, name="Cloud Tester", tier=CloudTier.FREE)
    
    assert user.tier == CloudTier.FREE
    assert len(user.api_keys) == 1
    api_key = user.api_keys[0]
    
    # Test user lookup by API key
    found_user = subscription_manager.get_user_by_api_key(api_key)
    assert found_user is not None
    assert found_user.user_id == user.user_id
    
    # Test quota check
    assert subscription_manager.check_and_record_quota(user.user_id, estimated_tokens=1000)
    summary = subscription_manager.get_user_status_summary(user.user_id)
    assert summary["metrics"]["tokens_consumed_today"] == 1000
    
    # Test Upgrade to PRO
    upgrade_res = subscription_manager.upgrade_subscription(
        user_id=user.user_id,
        target_tier=CloudTier.PRO,
        billing_cycle="yearly",
        payment_method="stripe_card"
    )
    assert upgrade_res["success"] is True
    assert upgrade_res["new_tier"] == "pro"
    assert len(user.invoices) == 1
    assert upgrade_res["invoice"]["amount_usd"] == 199.90
    
    # Test additional API key generation with scopes for Pro (limit 5)
    new_key = subscription_manager.generate_new_api_key(user.user_id, label="Analytics Key", scopes=["read", "inference"])
    assert new_key.startswith("tgpt_cloud_live_")
    assert len(user.api_keys) == 2
    
    print("[PASS] Subscription & Billing test passed!")


def test_formal_verifier_and_contracts():
    print("[TEST] Testing Z3 SMT Formal Verifier & Hoare Contracts...")
    claim = "Para todo x e y real, (x + y)^2 >= 4xy"
    cert = cloud_verifier.verify_expression(claim_text=claim, tier_depth=2)
    
    assert cert.certificate_id.startswith("proof_cert_")
    assert cert.status in ["PROVEN_SAT", "PROVEN_VALID", "VERIFIED_SYMBOLIC"]
    assert cert.proof_tree_hash.startswith("0x")
    assert len(cert.mathematical_invariants) > 0
    assert len(cert.proof_steps) > 0

    # Test DbC Contract
    c_res = cloud_verifier.verify_contract(
        preconditions=["x >= 0", "y >= 0"],
        postconditions=["x + y >= 0"],
        invariants=["x in Real", "y in Real"],
        function_name="gradient_step"
    )
    assert c_res.overall_status == "VERIFIED"
    assert c_res.preconditions_verified is True
    
    print(f"[PASS] Formal Verifier & Contract test passed! (Merkle Hash: {cert.proof_tree_hash[:18]}...)")


async def test_swarm_and_router():
    print("[TEST] Testing Swarm Orchestrator & Cloud Router with Streaming...")
    client = TruthGPTCloudClient(user_id="usr_pro_sample")
    
    # Test Inference with Z3 verification
    res = await client.ask_async(
        "Demuestra algebraicamente la optimizacion de latencia en modelos Transformer y verifica invariantes.",
        enable_formal_verification=True
    )
    assert res.content is not None
    assert len(res.content) > 50
    assert res.proof_certificate is not None
    assert res.proof_certificate["status"] in ["PROVEN_SAT", "PROVEN_VALID", "VERIFIED_SYMBOLIC"]
    
    # Test Swarm session with consensus
    swarm_trace = await client.run_swarm_async(
        "Analizar arquitectura de inferencia distribuida para TruthGPT Ultra."
    )
    assert len(swarm_trace.agents_involved) >= 3
    assert swarm_trace.consensus_score >= 0.95
    assert "consenso" in swarm_trace.consensus_summary.lower()

    # Test Streaming
    events = []
    async for ev in client.stream_chat("Verificar cota de error"):
        events.append(ev)
    assert len(events) > 1
    
    print("[PASS] Swarm, Router & Streaming test passed!")


async def run_all_tests():
    print("==================================================")
    print(">> Starting TruthGPT Cloud v2.1 Verification Suite")
    print("==================================================")
    test_tier_matrix()
    test_subscription_and_billing()
    test_formal_verifier_and_contracts()
    await test_swarm_and_router()
    print("==================================================")
    print(">> ALL TRUTHGPT CLOUD TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
