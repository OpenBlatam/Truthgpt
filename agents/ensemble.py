"""
Ensemble LLM strategies: consensus, parallel, race, majority, debate, bayesian.

Designed for unit testing without live API calls — merge/run helpers are pure or injectable.
Refactored to use the Strategy Pattern for modularity and maintainability.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

from .ensemble_strategies import EngineRun, StrategyFactory

ALL_ENSEMBLE_MODES = frozenset(
    {"consensus", "parallel", "race", "majority", "debate", "bayesian"}
)
MULTI_ENGINE_MODES = frozenset(
    {"consensus", "parallel", "majority", "debate", "bayesian"}
)

def merge_ensemble_responses(mode: str, runs: List[EngineRun]) -> str:
    """Merge per-engine runs into one AgentAction JSON string using Strategy Factory."""
    mode = (mode or "consensus").lower().strip()
    if mode not in ALL_ENSEMBLE_MODES:
        mode = "consensus"
        
    strategy = StrategyFactory.get_strategy(mode)
    if not runs:
        return json.dumps(
            {
                "thought": "Ensemble: no engine returned a response.",
                "final_answer": "Error: all engines failed in ensemble call.",
                "metadata": {"ensemble_mode": mode, "engines": []},
            },
            ensure_ascii=False,
        )
    return strategy.merge(runs, mode)

async def run_ensemble(
    mode: str,
    active: List[Dict[str, str]],
    prompt: str,
    run_engine: Callable,
    *,
    record_run: Optional[Callable[[str, str, float, int], None]] = None,
    **kwargs: Any,
) -> str:
    """
    Execute ensemble strategy.

    Args:
        mode: ensemble mode name
        active: [{"key", "label", "model"}, ...]
        prompt: user prompt
        run_engine: async (engine_key) -> (key, model, text, elapsed, tokens)
        record_run: optional callback(engine_key, model, elapsed, tokens)
    """
    mode = (mode or "consensus").lower().strip()
    if mode not in ALL_ENSEMBLE_MODES:
        mode = "consensus"

    async def _run_one(eng: Dict[str, str]) -> EngineRun:
        key = eng["key"]
        try:
            return await run_engine(key, eng, prompt, **kwargs)
        except Exception as exc:
            err = json.dumps(
                {
                    "thought": f"[{key}] error",
                    "final_answer": f"Error ({key}): {type(exc).__name__}: {str(exc)[:200]}",
                }
            )
            return key, eng.get("model", key), err, 0.0, 0

    if mode == "race":
        tasks = {
            eng["key"]: asyncio.create_task(_run_one(eng), name=f"ensemble-{eng['key']}")
            for eng in active
        }
        done, pending = await asyncio.wait(
            tasks.values(),
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        runs: List[EngineRun] = []
        winner_run: Optional[EngineRun] = None
        for task in done:
            try:
                run = task.result()
                runs.append(run)
                if winner_run is None or run[3] < winner_run[3]:
                    winner_run = run
            except Exception:
                continue

        if winner_run and record_run:
            record_run(winner_run[0], winner_run[1], winner_run[3], winner_run[4])

        return merge_ensemble_responses("race", runs if runs else ([winner_run] if winner_run else []))

    results = await asyncio.gather(
        *[_run_one(eng) for eng in active],
        return_exceptions=True,
    )
    runs = []
    for item in results:
        if isinstance(item, Exception):
            continue
        runs.append(item)
        if record_run:
            record_run(item[0], item[1], item[3], item[4])

    return merge_ensemble_responses(mode, runs)
