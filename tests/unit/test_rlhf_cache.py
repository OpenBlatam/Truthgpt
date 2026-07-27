"""Regression tests for the autonomous RLHF mission cache behavior.

The continuous/RLHF mission builds prompts dominated by a fixed boilerplate
("CRITICAL INSTRUCTION: ... provide a definitive 'final_answer'"), so
consecutive iterations are >0.92 cosine-similar. With the semantic cache on,
every iteration replayed the first cached answer ("always the same response").

The fix routes the self-refining loop through ``build_tiered_engine(
enable_cache=False)``, which sets ``APICostConfig.enable_semantic_cache=False``
so the cost cascade is preserved but answers are generated fresh each iteration.

These tests exercise the REAL ``APICostOptimizer`` + ``SemanticCache`` (no live
API) with the actual mission prompts, asserting the cache collapses responses
when on and never does when off.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.api_cost import APICostOptimizer, APICostConfig  # noqa: E402


def _build_optimizer(enable_cache: bool, cache_dir: str) -> APICostOptimizer:
    """Mirror how engine_registry._build_cost_optimized_engine configures the
    optimizer, toggling only the semantic cache (the line the fix flips)."""
    cfg = APICostConfig(daily_budget_usd=1_000_000.0)
    cfg.model_cascade.confidence_threshold = 0.7
    cfg.enable_semantic_cache = enable_cache
    cfg.enable_prompt_compression = False  # keep prompts intact for the test
    opt = APICostOptimizer(cfg)
    opt.cache.cache_dir = cache_dir  # isolate from the real on-disk cache db
    return opt


def _mission_prompts() -> list[str]:
    """Reproduce the prompts handle_continuous_mission builds per iteration."""
    query = "optimize tool-call chains for the agent"
    boiler = (
        "\nCRITICAL INSTRUCTION: You are running in a fully autonomous background "
        "mission. DO NOT ask the user for clarification or wait for input. Make "
        "your best assumptions, execute the necessary actions, and provide a "
        "definitive 'final_answer'."
    )
    prompts = [f"Execute next step for: {query}{boiler}"]
    for i in range(1, 4):
        findings = f"Latest findings: iteration {i} produced result variant {i}."
        prompts.append(f"Execute next step for: Original: {query}\n{findings}{boiler}")
    return prompts


async def _run(enable_cache: bool, cache_dir: str) -> list[str]:
    counter = {"n": 0}

    async def stub_model(prompt: str, model=None, **kw) -> str:
        counter["n"] += 1
        return f"FRESH#{counter['n']}"

    opt = _build_optimizer(enable_cache, cache_dir)
    ladder = ["cheap-model", "top-model"]
    return [await opt.call(p, stub_model, models=ladder) for p in _mission_prompts()]


@pytest.mark.asyncio
async def test_cache_enabled_replays_responses(tmp_path):
    """Bug repro: with the semantic cache on, near-identical RLHF prompts
    collapse to a single replayed answer."""
    responses = await _run(enable_cache=True, cache_dir=str(tmp_path / "on"))
    assert len(responses) == 4
    assert len(set(responses)) < len(responses), (
        "expected the semantic cache to replay a cached answer across iterations"
    )


@pytest.mark.asyncio
async def test_cache_disabled_yields_fresh_responses(tmp_path):
    """Fix: with enable_cache=False the model is invoked fresh every iteration,
    so no two iterations share a response."""
    responses = await _run(enable_cache=False, cache_dir=str(tmp_path / "off"))
    assert len(responses) == 4
    assert len(set(responses)) == len(responses), (
        "expected a fresh generation per iteration when the cache is disabled"
    )


def test_engine_registry_disables_cache_for_rlhf():
    """The continuous RLHF mission must request the cache-free engine."""
    src = (ROOT / "interface" / "swarm" / "missions.py").read_text(encoding="utf-8")
    assert "enable_cache=False" in src, (
        "handle_continuous_mission should build its engine with enable_cache=False"
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0.85", 0.85),
        ("Score: 0.7", 0.7),
        (".9", 0.9),
        ("1", 1.0),
        ("the rating is 1.0", 1.0),
        ("no number here", 0.5),     # falls back to default
        ("8/10", 0.5),               # out-of-range integers ignored
        ("1.5 then 0.3", 0.3),       # skips out-of-range, picks first in [0,1]
    ],
)
def test_parse_reward(text, expected):
    """The reward parser tolerates messy judgments and clamps to [0, 1]."""
    from src.truthgpt.interface.swarm.missions import _parse_reward
    assert _parse_reward(text) == pytest.approx(expected)


@pytest.mark.asyncio
async def test_background_mission_carries_history_across_cycles():
    """Each background cycle must build on prior cycles, not restart from the
    bare query — otherwise successive cycles repeat the same work."""
    from types import SimpleNamespace
    from src.truthgpt.interface.swarm.missions import BackgroundMission

    seen_prompts: list[str] = []
    holder: dict = {}

    class FakeAgent:
        def __init__(self, config=None, llm_engine=None):
            self.config = config
            self.llm_engine = llm_engine

        async def process(self, prompt, context=None):
            seen_prompts.append(prompt)
            n = len(seen_prompts)
            if n >= 2:  # stop the loop after the second cycle completes
                holder["mission"].status = "Stopped"
            return SimpleNamespace(content=f"cycle-{n}-finding")

    mission = BackgroundMission(
        name="t", query="optimize X", interval=0,
        team=["worker"], agents_map={"worker": FakeAgent},
        config=None, llm=None, context={"user_id": "t"},
    )
    holder["mission"] = mission

    await mission.run_loop()

    assert len(seen_prompts) == 2
    # Cycle 1 starts bare from the mission query.
    assert seen_prompts[0] == "optimize X"
    # Cycle 2 carries prior-cycle memory and the advance directive.
    assert "cycle-1-finding" in seen_prompts[1]
    assert "ADVANCING" in seen_prompts[1]
    assert "do not repeat" in seen_prompts[1]
