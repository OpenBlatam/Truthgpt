"""
Unit tests for ensemble LLM modes (consensus, parallel, race, majority, debate, bayesian).

No live API calls — uses mocked engine runners.
"""

from __future__ import annotations

import asyncio
import json
import sys
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
elif sys.path[0] != str(ROOT):
    sys.path.remove(str(ROOT))
    sys.path.insert(0, str(ROOT))

# Prevent shadowing of the local agents module on systems with a parent agents package
local_agents = ROOT / "agents"
if "agents" in sys.modules:
    agents_mod = sys.modules["agents"]
    if hasattr(agents_mod, "__path__"):
        if str(local_agents) not in agents_mod.__path__:
            agents_mod.__path__.insert(0, str(local_agents))

# Force-import critical local modules into sys.modules to prevent shadowing on sub-imports
for mod_name in ["agents.ssl_context", "agents.engines", "agents.ensemble"]:
    rel_path = mod_name.split(".")[-1] + ".py"
    full_path = ROOT / "agents" / rel_path
    if full_path.exists():
        spec = importlib.util.spec_from_file_location(mod_name, str(full_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

from agents.ensemble import (  # noqa: E402
    ALL_ENSEMBLE_MODES,
    merge_ensemble_responses,
    parse_agent_json,
    run_ensemble,
)


def _agent(thought: str, final: str, confidence: float | None = None) -> str:
    payload: dict = {"thought": thought, "final_answer": final}
    if confidence is not None:
        payload["confidence"] = confidence
    return json.dumps(payload)


def _runs(*items: tuple) -> list:
    """(key, model, json_str, elapsed, tokens)"""
    return list(items)


@pytest.mark.parametrize("mode", sorted(ALL_ENSEMBLE_MODES))
def test_all_modes_produce_valid_json(mode: str):
    runs = _runs(
        ("deepseek", "ds-model", _agent("t1", "The capital of France is Paris."), 2.0, 40),
        ("claude", "cl-model", _agent("t2", "The capital of France is Paris."), 3.0, 50),
    )
    out = merge_ensemble_responses(mode, runs)
    data = json.loads(out)
    assert "thought" in data
    assert "final_answer" in data
    assert data["final_answer"]
    assert data["metadata"]["ensemble_mode"] == mode
    assert set(data["metadata"]["engines"]) == {"deepseek", "claude"}


def test_parse_agent_json_strips_markdown_fence():
    raw = '```json\n{"thought": "x", "final_answer": "y"}\n```'
    data = parse_agent_json(raw)
    assert data["final_answer"] == "y"


def test_consensus_picks_aligned_cluster():
    runs = _runs(
        ("deepseek", "ds", _agent("a", "Answer A same topic."), 1.0, 10),
        ("claude", "cl", _agent("b", "Answer A same topic."), 2.0, 10),
        ("google", "gg", _agent("c", "Completely different xyz nonsense."), 3.0, 10),
    )
    out = json.loads(merge_ensemble_responses("consensus", runs))
    assert "Answer A" in out["final_answer"]
    assert out["metadata"]["winner"] in ("deepseek", "claude")


def test_majority_two_vs_one():
    runs = _runs(
        ("deepseek", "ds", _agent("a", "Yes, deploy on Monday."), 1.0, 10),
        ("claude", "cl", _agent("b", "Yes, deploy on Monday."), 2.0, 10),
        ("google", "gg", _agent("c", "No, wait until Friday."), 3.0, 10),
    )
    out = json.loads(merge_ensemble_responses("majority", runs))
    assert "Monday" in out["final_answer"]
    assert out["metadata"]["winner"] in ("deepseek", "claude")


def test_parallel_includes_all_sections():
    runs = _runs(
        ("deepseek", "ds", _agent("a", "DeepSeek answer."), 1.0, 10),
        ("claude", "cl", _agent("b", "Claude answer."), 2.0, 10),
    )
    out = json.loads(merge_ensemble_responses("parallel", runs))
    assert "### deepseek" in out["final_answer"]
    assert "### claude" in out["final_answer"]
    assert "DeepSeek answer" in out["final_answer"]
    assert "Claude answer" in out["final_answer"]
    assert "parallel_outputs" in out["metadata"]


def test_race_selects_fastest_engine():
    runs = _runs(
        ("deepseek", "ds", _agent("fast", "Winner from deepseek."), 0.5, 10),
        ("claude", "cl", _agent("slow", "Loser from claude."), 5.0, 10),
    )
    out = json.loads(merge_ensemble_responses("race", runs))
    assert out["metadata"]["winner"] == "deepseek"
    assert "deepseek" in out["final_answer"]


def test_bayesian_prefers_high_confidence():
    runs = _runs(
        ("deepseek", "ds", _agent("low", "Low confidence answer.", 0.2), 1.0, 10),
        ("claude", "cl", _agent("high", "High confidence answer.", 0.95), 2.0, 10),
    )
    out = json.loads(merge_ensemble_responses("bayesian", runs))
    assert out["metadata"]["winner"] == "claude"
    assert "High confidence" in out["final_answer"]


def test_debate_marks_disagreement():
    runs = _runs(
        ("deepseek", "ds", _agent("a", "Use PostgreSQL for storage."), 1.0, 10),
        ("claude", "cl", _agent("b", "Use MongoDB for flexibility."), 2.0, 10),
    )
    out = json.loads(merge_ensemble_responses("debate", runs))
    assert "Debate transcript" in out["final_answer"]
    assert out["metadata"]["aligned"] is False
    assert "Verdict" in out["final_answer"]


def test_empty_runs_error_payload():
    out = json.loads(merge_ensemble_responses("consensus", []))
    assert "Error" in out["final_answer"]


@pytest.mark.asyncio
async def test_run_ensemble_consensus_mocked():
    active = [
        {"key": "alpha", "label": "alpha", "model": "alpha-m"},
        {"key": "beta", "label": "beta", "model": "beta-m"},
    ]

    async def fake_run(key, eng, prompt, **kwargs):
        await asyncio.sleep(0.01 if key == "alpha" else 0.02)
        return (
            key,
            eng["model"],
            _agent(key, f"Response from {key} for: {prompt[:20]}"),
            0.01,
            12,
        )

    recorded = []

    def record(key, model, elapsed, tokens):
        recorded.append((key, model, elapsed, tokens))

    result = await run_ensemble(
        "consensus",
        active,
        "What is 2+2?",
        fake_run,
        record_run=record,
    )
    data = json.loads(result)
    assert data["final_answer"]
    assert len(recorded) == 2
    assert {r[0] for r in recorded} == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_run_ensemble_race_cancels_slow_mocked():
    active = [
        {"key": "fast", "label": "fast", "model": "f"},
        {"key": "slow", "label": "slow", "model": "s"},
    ]

    async def fake_run(key, eng, prompt, **kwargs):
        if key == "fast":
            await asyncio.sleep(0.01)
            return key, eng["model"], _agent("f", "Fast wins."), 0.01, 5
        await asyncio.sleep(2.0)
        return key, eng["model"], _agent("s", "Slow loses."), 2.0, 5

    recorded = []

    result = await run_ensemble(
        "race",
        active,
        "ping",
        fake_run,
        record_run=lambda k, m, e, t: recorded.append(k),
    )
    data = json.loads(result)
    assert data["metadata"]["winner"] == "fast"
    assert len(recorded) == 1
    assert recorded[0] == "fast"


@pytest.mark.asyncio
async def test_registry_builds_ensemble_for_multi_engine(monkeypatch):
    from agents.engines import EngineRegistry, _benchmark_run_stats

    registry = EngineRegistry()
    registry._providers.clear()

    class MockProvider:
        def __init__(self, key, model, delay=0.01):
            self.model = model
            self.api_key = "sk-test"
            self.key = key
            self.delay = delay

        async def generate(self, prompt, **kwargs):
            await asyncio.sleep(self.delay)
            return _agent(self.key, f"Answer from {self.key}")

    registry.register("deepseek", MockProvider("deepseek", "ds-v1", 0.01))
    registry.register("claude", MockProvider("claude", "cl-v1", 0.02))

    monkeypatch.setattr(
        "agents.engines._get_user_prefs",
        lambda: {
            "preferred_engine": "deepseek,claude",
            "ensemble_mode": "parallel",
            "api_keys": {"deepseek": "k1", "anthropic": "k2"},
        },
    )
    monkeypatch.setattr(
        "agents.engines._load_api_keys_from_prefs",
        lambda: {"DEEPSEEK_API_KEY": "k1", "ANTHROPIC_API_KEY": "k2"},
    )

    engine = registry.get_engine(None)
    assert engine is not None
    assert getattr(engine, "is_ensemble", False) is True
    assert engine.ensemble_mode == "parallel"

    _benchmark_run_stats.clear()
    out = await engine("test prompt")
    data = json.loads(out)
    assert "### deepseek" in data["final_answer"]
    assert "### claude" in data["final_answer"]
    assert len(_benchmark_run_stats) == 2


@pytest.mark.asyncio
async def test_registry_race_mode(monkeypatch):
    from agents.engines import EngineRegistry

    registry = EngineRegistry()
    registry._providers.clear()

    class MockProvider:
        def __init__(self, key, delay):
            self.key = key
            self.model = f"{key}-m"
            self.api_key = "sk-test"
            self.delay = delay

        async def generate(self, prompt, **kwargs):
            await asyncio.sleep(self.delay)
            return _agent(self.key, f"Winner {self.key}")

    registry._providers["deepseek"] = MockProvider("deepseek", 0.05)
    registry._providers["claude"] = MockProvider("claude", 0.5)

    monkeypatch.setattr(
        "agents.engines._get_user_prefs",
        lambda: {
            "preferred_engine": "deepseek,claude",
            "ensemble_mode": "race",
            "api_keys": {"deepseek": "k1", "anthropic": "k2"},
        },
    )
    monkeypatch.setattr(
        "agents.engines._load_api_keys_from_prefs",
        lambda: {"DEEPSEEK_API_KEY": "k1", "ANTHROPIC_API_KEY": "k2"},
    )

    engine = registry.get_engine(None)
    assert engine.ensemble_mode == "race"
    out = await engine("quick")
    data = json.loads(out)
    assert data["metadata"]["winner"] == "deepseek"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["consensus", "majority", "debate", "bayesian", "parallel"])
async def test_registry_all_merge_modes(monkeypatch, mode: str):
    from agents.engines import EngineRegistry

    registry = EngineRegistry()
    registry._providers.clear()

    class MockProvider:
        def __init__(self, key, final):
            self.key = key
            self.model = f"{key}-model"
            self.api_key = "sk-test"
            self.final = final

        async def generate(self, prompt, **kwargs):
            return _agent(self.key, self.final)

    registry._providers["deepseek"] = MockProvider(
        "deepseek", "Agree on option A for production."
    )
    registry._providers["claude"] = MockProvider(
        "claude", "Agree on option A for production."
    )

    monkeypatch.setattr(
        "agents.engines._get_user_prefs",
        lambda: {
            "preferred_engine": "deepseek,claude",
            "ensemble_mode": mode,
            "api_keys": {"deepseek": "k1", "anthropic": "k2"},
        },
    )
    monkeypatch.setattr(
        "agents.engines._load_api_keys_from_prefs",
        lambda: {"DEEPSEEK_API_KEY": "k1", "ANTHROPIC_API_KEY": "k2"},
    )

    engine = registry.get_engine(None)
    assert engine.ensemble_mode == mode
    out = await engine("Choose deployment strategy")
    data = json.loads(out)
    assert data["final_answer"]
    assert data["metadata"]["ensemble_mode"] == mode
