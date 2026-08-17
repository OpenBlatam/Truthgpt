"""
Comprehensive Unit Tests for Marketing AI Module
===================================================
Tests all features, classes, agents, models, publisher, connectors, generators,
and master terminal suite in optimization_core/marketing.
"""

import os
import shutil
import pytest
import asyncio

from marketing import (
    PERSONAS,
    CHANNEL_SPECS,
    FUNNEL_STAGES,
    CIALDINI_PRINCIPLES,
    ConsumerFatigueModel,
    CausalForestAttributor,
    ContentGenerators,
    ProductionPublisher,
    AdPlatformManager,
    PersuasionCopywriterAgent,
    CausalForestAnalystAgent,
    BudgetOptimizerAgent,
    IntegratedMarketingAITerminal,
    OpusClipAIEngine,
    AIBRollSoundEngine,
    SocialMediaPostMonitorEngine,
    ViralThumbnailGenerator,
)


@pytest.fixture
def tmp_dir(tmp_path):
    d = tmp_path / "marketing_test_sandbox"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def test_knowledge_base_integrity():
    assert "ceo_b2b" in PERSONAS
    assert "ecommerce_manager" in PERSONAS
    assert "meta_ad" in CHANNEL_SPECS
    assert "tofu" in FUNNEL_STAGES
    assert "reciprocity" in CIALDINI_PRINCIPLES
    assert len(CIALDINI_PRINCIPLES) == 6


def test_consumer_fatigue_model():
    model = ConsumerFatigueModel(base_engagement=0.70, decay_rate=0.10, recovery_rate=0.08)
    fatigue = model.compute_fatigue_score(days_since_last=2.0, total_contacts=5)
    assert 0.0 <= fatigue <= 1.0

    pred = model.predict_engagement(days_since_last=3.0, total_contacts=2, content_novelty=0.8)
    assert "engagement_probability" in pred
    assert "fatigue_score" in pred
    assert 0.0 <= pred["engagement_probability"] <= 1.0

    schedule = model.optimal_send_schedule(num_emails=3, campaign_days=10)
    assert len(schedule) == 3
    assert schedule[0]["day"] <= schedule[1]["day"] <= schedule[2]["day"]


def test_causal_forest_attributor():
    import torch
    import torch.nn as nn

    class MockMoE(nn.Module):
        def forward(self, x):
            return torch.ones(x.size(0), 10, 256)

    moe = MockMoE()
    attributor = CausalForestAttributor(moe_layer=moe, num_trees=50)

    res = attributor.estimate_segment_uplift(
        persona_key="ceo_b2b",
        stage="bofu",
        channels=["email", "linkedin_ad"],
    )
    assert res["segment"] == "ceo_b2b×bofu"
    assert "channel_effects" in res
    assert "email" in res["channel_effects"]
    assert "treatment_effect" in res["channel_effects"]["email"]


def test_content_generators():
    persona = PERSONAS["ceo_b2b"]
    angle = {
        "domain": "SaaS Sales",
        "benefit": "aumentar el flujo de leads calificados",
        "hook": "Sistema de IA",
        "gift": "Guía de ROI",
    }

    script = ContentGenerators.build_video_script("TestProduct", persona, angle)
    assert script["product"] == "TestProduct"
    assert "script" in script

    wa = ContentGenerators.build_whatsapp_sequence("TestProduct", persona, angle)
    assert len(wa["messages"]) == 3

    matrix = ContentGenerators.build_multi_angle_matrix("TestProduct", persona, angle)
    assert "emotional" in matrix["angles"]
    assert "logical_roi" in matrix["angles"]
    assert "zero_risk" in matrix["angles"]

    comp = ContentGenerators.build_competitor_ad("TestProduct", "CompX", angle)
    assert comp["competitor"] == "CompX"

    seo = ContentGenerators.build_seo_article("TestProduct", persona, angle)
    assert "title" in seo
    assert "meta_description" in seo

    cold = ContentGenerators.build_cold_email("TestProduct", persona, angle)
    assert cold["framework"] == "PAS (Problem-Agitate-Solve)"

    web = ContentGenerators.build_webinar_funnel("TestProduct", persona, angle)
    assert "webinar_title" in web

    soc = ContentGenerators.build_social_calendar("TestProduct", persona, angle)
    assert len(soc["calendar"]) == 3

    churn = ContentGenerators.build_churn_prevention("TestProduct", persona, angle)
    assert "predicted_churn_reduction" in churn


def test_production_publisher(tmp_dir):
    campaign_data = {
        "campaigns": [
            {
                "channel": "meta_ad",
                "headline": "Headline Test",
                "body": "Body Test",
                "predicted_ctr": "5.2%",
                "cta": "Comprar",
            }
        ]
    }
    report_file = ProductionPublisher.export_report("ProductX", campaign_data, output_dir=tmp_dir)
    assert os.path.exists(report_file)
    assert os.path.getsize(report_file) > 0

    video_res = {"estimated_retention_rate": "75%", "script": "Test Script"}
    wa_res = {"messages": []}
    ads_res = campaign_data
    cold_res = {"subject": "Test Subj", "body": "Test Body"}
    soc_res = {"calendar": []}

    bundle_dir = ProductionPublisher.create_production_bundle(
        "ProductX", video_res, wa_res, ads_res, cold_res, soc_res, output_parent_dir=tmp_dir
    )
    assert os.path.exists(bundle_dir)
    assert os.path.exists(os.path.join(bundle_dir, "01_script_video_tiktok_reels.txt"))
    assert os.path.exists(os.path.join(bundle_dir, "MANIFEST_PRODUCCION.json"))


def test_ad_platform_manager(tmp_dir):
    mgr = AdPlatformManager()
    status = mgr.get_all_platforms_status()
    assert len(status) == 4

    calib_meta = mgr.get_calibration_factor("meta_ad")
    assert calib_meta >= 1.0

    cache_file = os.path.join(tmp_dir, "test_ads_cache.json")
    saved_path = mgr.sync_and_save_cache(output_path=cache_file)
    assert os.path.exists(saved_path)


@pytest.mark.asyncio
async def test_copywriter_agent():
    agent = PersuasionCopywriterAgent()
    res = await agent.process("AI Software", {"persona": "ceo_b2b", "stage": "tofu"})
    assert res["status"] == "success"
    assert len(res["campaigns"]) > 0

    script = await agent.generate_video_script("AI Software", "ceo_b2b")
    assert "script" in script

    wa = await agent.generate_whatsapp_sequence("AI Software", "ceo_b2b")
    assert len(wa["messages"]) == 3


@pytest.mark.asyncio
async def test_causal_analyst_and_budget_agents():
    analyst = CausalForestAnalystAgent()
    res_analyst = await analyst.process("Growth Campaign", {"persona": "ecommerce_manager", "stage": "bofu"})
    assert res_analyst["enhanced_method"] == "causal_forest_hte"

    budget_agent = BudgetOptimizerAgent()
    res_budget = await budget_agent.process(
        "Budget Task",
        {
            "budget": 5000,
            "channels": ["meta_ad", "google_ad", "email"],
            "uplift_signals": {
                "email": {"treatment_effect": 0.45, "recommendation": "INVEST"}
            },
        },
    )
    assert res_budget["total_budget"] == 5000
    assert "allocation" in res_budget
    assert "email" in res_budget["allocation"]


def test_integrated_marketing_ai_terminal(tmp_dir):
    terminal = IntegratedMarketingAITerminal()
    assert terminal.copy_agent is not None
    assert terminal.analyst_agent is not None
    assert terminal.budget_agent is not None

    camps = terminal.cmd_generate("DemoProduct", "ceo_b2b", "tofu")
    assert len(camps) > 0

    winner = terminal.cmd_evaluate(camps)
    assert winner is not None

    causal_res = terminal.cmd_causal("DemoProduct", "bofu", "ceo_b2b")
    assert "segment" in causal_res
