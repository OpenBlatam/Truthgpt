"""
Unit Tests for Marketing AI & OpusClip Engine v6.0
"""

import pytest
import os
import shutil
from marketing import (
    OpusClipAIEngine,
    AIBRollSoundEngine,
    SocialMediaPostMonitorEngine,
    ViralThumbnailGenerator,
    IntegratedMarketingAITerminal
)

@pytest.fixture
def temp_output_dir(tmp_path):
    d = tmp_path / "opus_test_output"
    d.mkdir()
    return str(d)

def test_thumbnail_generator(temp_output_dir):
    cover_file = os.path.join(temp_output_dir, "test_cover.png")
    res = ViralThumbnailGenerator.create_thumbnail("Test Video Viral", 95, cover_file)
    assert os.path.exists(res)
    assert os.path.getsize(res) > 0

def test_broll_sound_engine(temp_output_dir):
    engine = AIBRollSoundEngine(sfx_dir=os.path.join(temp_output_dir, "sfx"))
    enhanced = engine.enhance_clip({"title": "Test SaaS", "transcript": [{"start": 0.0, "text": "Dinero y conversiones"}]})
    assert "brolls_inserted" in enhanced
    assert "sfx_timeline" in enhanced
    assert len(enhanced["sfx_timeline"]) > 0
    assert os.path.exists(enhanced["sfx_timeline"][0]["wav_file"])

def test_social_media_post_monitor():
    monitor = SocialMediaPostMonitorEngine()
    analytics = monitor.fetch_live_clip_analytics()
    assert len(analytics) >= 3
    recs = monitor.generate_strategy_recommendations()
    assert "top_performing_clip" in recs
    assert "recommendations" in recs

def test_opus_clip_ai_engine(temp_output_dir):
    clipper = OpusClipAIEngine(output_dir=temp_output_dir)
    res = clipper.process("https://www.youtube.com/watch?v=unit_test_demo", auto_mode=True, max_clips=2)
    assert "clips_generated" in res
    assert len(res["clips_generated"]) == 2
    assert os.path.exists(res["clips_generated"][0]["cover_image_pil"])
