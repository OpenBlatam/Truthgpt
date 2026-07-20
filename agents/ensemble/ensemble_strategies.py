import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from .ensemble_utils import (
    _cluster_by_similarity,
    _extract_confidence,
    _extract_final,
    _extract_thought,
    _pick_largest_cluster,
    _similarity,
    parse_agent_json,
)

# Run tuple: (engine_key, model_name, raw_text, elapsed_sec, token_estimate)
EngineRun = Tuple[str, str, str, float, int]


def _empty_response(mode: str) -> str:
    """Standard error JSON when no engine returned a response."""
    return json.dumps({
        "thought": "Ensemble: no engine returned a response.",
        "final_answer": "Error: all engines failed in ensemble call.",
        "metadata": {"ensemble_mode": mode, "engines": []},
    }, ensure_ascii=False)

class EnsembleStrategy(ABC):
    @abstractmethod
    def merge(self, runs: List[EngineRun], mode: str) -> str:
        """Merge per-engine runs into one AgentAction JSON string."""
        pass

    def _prepare_parsed(self, runs: List[EngineRun]) -> Tuple[List[Tuple[str, str, Dict[str, Any]]], str]:
        parsed: List[Tuple[str, str, Dict[str, Any]]] = []
        for key, model, text, _elapsed, _tokens in runs:
            if not text:
                continue
            data = parse_agent_json(text)
            parsed.append((key, model, data))

        if not parsed:
            return [], ""

        engine_list = [f"{k} ({m})" for k, m, _ in parsed]
        header = f"Ensemble [{self.name()}] from {', '.join(engine_list)}"
        return parsed, header

    def _recover_final(
        self,
        merged: str,
        winner_key: str,
        parsed: List[Tuple[str, str, Dict[str, Any]]],
    ) -> str:
        """Never emit an empty final_answer.

        A common engine failure mode is to put all useful content in 'thought'
        and leave 'final_answer' blank — which then scores ~0 downstream and
        triggers endless self-correction. When that happens, recover the
        winning engine's reasoning so the mission has something to act on.
        """
        if merged and merged.strip():
            return merged
        for key, _model, data in parsed:
            if key == winner_key:
                return _extract_thought(data)
        return _extract_thought(parsed[0][2]) if parsed else ""

    @classmethod
    def name(cls) -> str:
        return "base"


class ParallelStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "parallel"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        sections = []
        thought_lines = []
        for key, model, data in parsed:
            thought = _extract_thought(data)
            final = _extract_final(data)
            thought_lines.append(f"[{key}/{model}] {thought}".strip())
            sections.append(f"### {key} ({model})\n{final or '(no final_answer)'}")

        return json.dumps(
            {
                "thought": f"{header}:\n" + "\n".join(thought_lines),
                "final_answer": "\n\n---\n\n".join(sections),
                "metadata": {
                    "ensemble_mode": mode,
                    "engines": [k for k, _, _ in parsed],
                    "parallel_outputs": {k: _extract_final(d) for k, _, d in parsed},
                },
            },
            ensure_ascii=False,
        )


class RaceStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "race"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        successful = [r for r in runs if r[2]]
        if not successful:
            return _empty_response(mode)
            
        winner = min(successful, key=lambda r: r[3])
        key, model, text, elapsed, tokens = winner
        data = parse_agent_json(text)
        return json.dumps(
            {
                "thought": f"{header} — winner [{key}/{model}] in {elapsed:.2f}s:\n"
                + _extract_thought(data),
                "final_answer": _extract_final(data) or _extract_thought(data) or text,
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": key,
                    "winner_model": model,
                    "elapsed": elapsed,
                    "tokens": tokens,
                    "engines": [k for k, _, _ in parsed],
                },
            },
            ensure_ascii=False,
        )


class MajorityStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "majority"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        finals = [(k, _extract_final(d)) for k, _, d in parsed if _extract_final(d)]
        thought_lines = [f"[{k}/{m}] {_extract_thought(d)}" for k, m, d in parsed]

        vote_count = 1
        if len(finals) <= 1:
            merged = finals[0][1] if finals else _extract_final(parsed[0][2])
            winner_key = finals[0][0] if finals else parsed[0][0]
        else:
            clusters = _cluster_by_similarity(finals)
            winner_key, merged = _pick_largest_cluster(clusters)
            vote_count = max(len(c) for c in clusters)
            
        vote_info = (
            f"majority vote ({vote_count}/{len(finals)} engines aligned)"
            if len(finals) > 1
            else "single engine"
        )

        merged = self._recover_final(merged, winner_key, parsed)

        return json.dumps(
            {
                "thought": f"{header} — {vote_info}, selected [{winner_key}]:\n"
                + "\n".join(thought_lines),
                "final_answer": merged,
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": winner_key,
                    "engines": [k for k, _, _ in parsed],
                },
            },
            ensure_ascii=False,
        )


class DebateStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "debate"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        positions = []
        for key, model, data in parsed:
            final = _extract_final(data)
            thought = _extract_thought(data)
            positions.append(
                {
                    "engine": key,
                    "model": model,
                    "position": final or thought,
                    "thought": thought,
                }
            )

        if len(positions) == 1:
            p = positions[0]
            return json.dumps(
                {
                    "thought": f"{header}:\n[{p['engine']}] {p['thought']}",
                    "final_answer": p["position"],
                    "metadata": {"ensemble_mode": mode, "engines": [p["engine"]]},
                },
                ensure_ascii=False,
            )

        clusters = _cluster_by_similarity(
            [(p["engine"], p["position"]) for p in positions],
            threshold=0.5,
        )
        majority_key, majority_answer = _pick_largest_cluster(clusters)

        debate_lines = ["## Debate transcript"]
        for p in positions:
            debate_lines.append(f"**{p['engine']}** ({p['model']}): {p['position'][:800]}")

        disagreements = len(clusters) > 1
        if disagreements:
            debate_lines.append("\n## Reconciliation")
            debate_lines.append(
                f"Engines disagreed ({len(clusters)} positions). "
                f"Verdict follows the largest aligned group, led by **{majority_key}**."
            )
            alt = [c[0][0] for c in clusters if c[0][0] != majority_key]
            if alt:
                debate_lines.append(f"Minority/divergent: {', '.join(alt)}.")
        else:
            debate_lines.append("\n## Reconciliation\nAll engines reached aligned conclusions.")

        return json.dumps(
            {
                "thought": f"{header}:\n" + "\n".join(
                    f"[{p['engine']}] {p['thought'][:200]}" for p in positions
                ),
                "final_answer": "\n".join(debate_lines) + f"\n\n**Verdict:** {majority_answer}",
                "metadata": {
                    "ensemble_mode": mode,
                    "engines": [p["engine"] for p in positions],
                    "aligned": not disagreements,
                    "winner": majority_key,
                },
            },
            ensure_ascii=False,
        )


class BayesianStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "bayesian"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        weighted: List[Tuple[str, str, Dict[str, Any], float]] = []
        for key, model, data in parsed:
            conf = _extract_confidence(data)
            weighted.append((key, model, data, conf))

        total = sum(w for *_, w in weighted) or 1.0
        best = max(weighted, key=lambda x: x[3])
        key, model, data, conf = best

        breakdown = ", ".join(f"{k}={w:.2f}" for k, _, _, w in weighted)
        thought_lines = [f"[{k}/{m}] (p={w:.2f}) {_extract_thought(d)}" for k, m, d, w in weighted]

        return json.dumps(
            {
                "thought": f"{header} — Bayesian weights [{breakdown}], selected [{key}]:\n"
                + "\n".join(thought_lines),
                "final_answer": _extract_final(data) or _extract_thought(data),
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": key,
                    "winner_model": model,
                    "confidence": conf,
                    "weights": {k: w / total for k, _, _, w in weighted},
                    "engines": [k for k, _, _ in parsed],
                },
            },
            ensure_ascii=False,
        )


class ConsensusStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "consensus"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        finals = [(k, _extract_final(d), _extract_confidence(d)) for k, _, d in parsed]
        thought_lines = [f"[{k}/{m}] {_extract_thought(d)}" for k, m, d in parsed]

        if len(finals) == 1:
            k, ans, _ = finals[0]
            merged, winner = ans, k
        else:
            clusters: List[List[Tuple[str, str, float]]] = []
            for key, final, conf in finals:
                if not final:
                    continue
                placed = False
                for cluster in clusters:
                    if _similarity(final, cluster[0][1]) >= 0.55:
                        cluster.append((key, final, conf))
                        placed = True
                        break
                if not placed:
                    clusters.append([(key, final, conf)])

            if not clusters:
                k, _, d = parsed[0]
                merged, winner = _extract_final(d), k
            else:
                best_cluster = max(
                    clusters,
                    key=lambda c: (len(c), sum(x[2] for x in c) / len(c)),
                )
                winner, merged, _ = max(best_cluster, key=lambda x: (x[2], len(x[1])))

        merged = self._recover_final(merged, winner, parsed)

        return json.dumps(
            {
                "thought": f"{header} — consensus via [{winner}]:\n" + "\n".join(thought_lines),
                "final_answer": merged,
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": winner,
                    "engines": [k for k, _, _ in parsed],
                },
            },
            ensure_ascii=False,
        )


class ElasticStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "elastic"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        # Elastic Reasoning separates thought/solution with budget awareness
        best_run = max(parsed, key=lambda x: len(_extract_thought(x[2])))
        key, model, data = best_run
        
        thought_lines = [
            f"Phase 1 (Exploration - {k}/{m}): {_extract_thought(d)[:300]}..." 
            for k, m, d in parsed
        ]
        
        return json.dumps(
            {
                "thought": f"{header} — Elastic Reasoning. Selected [{key}] for Phase 2 (Solution):\n"
                + "\n".join(thought_lines) + f"\n\nDeep Thought via {key}:\n{_extract_thought(data)}",
                "final_answer": self._recover_final(_extract_final(data), key, parsed),
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": key,
                    "engines": [k for k, _, _ in parsed],
                    "elastic_budget_spent": sum(r[4] for r in runs)
                },
            },
            ensure_ascii=False,
        )


class MCTSStrategy(EnsembleStrategy):
    @classmethod
    def name(cls) -> str:
        return "mcts"

    def merge(self, runs: List[EngineRun], mode: str) -> str:
        parsed, header = self._prepare_parsed(runs)
        if not parsed:
            return _empty_response(mode)

        # MCT Self-Refine simulates a Monte Carlo Tree Search
        # by evaluating generated branches and selecting the one with the best reward heuristic (confidence * thought length)
        scored_nodes = []
        for key, model, data in parsed:
            conf = _extract_confidence(data)
            thought_len = len(_extract_thought(data))
            reward = conf * (1.0 + (min(thought_len, 2000) / 2000.0))
            scored_nodes.append((key, model, data, reward))

        best_node = max(scored_nodes, key=lambda x: x[3])
        winner_key, winner_model, winner_data, winner_score = best_node
        
        tree_log = [f"Node [{k}/{m}] -> Reward: {r:.2f}" for k, m, d, r in scored_nodes]

        return json.dumps(
            {
                "thought": f"{header} — MCT Self-Refine path evaluation:\n"
                + "\n".join(tree_log) + f"\n\nSelected optimal path [{winner_key}] with score {winner_score:.2f}:\n{_extract_thought(winner_data)}",
                "final_answer": self._recover_final(_extract_final(winner_data), winner_key, parsed),
                "metadata": {
                    "ensemble_mode": mode,
                    "winner": winner_key,
                    "engines": [k for k, _, _ in parsed],
                    "mcts_evaluations": len(scored_nodes),
                    "best_score": winner_score
                },
            },
            ensure_ascii=False,
        )


class StrategyFactory:
    _strategies: Dict[str, EnsembleStrategy] = {
        "parallel": ParallelStrategy(),
        "race": RaceStrategy(),
        "majority": MajorityStrategy(),
        "debate": DebateStrategy(),
        "bayesian": BayesianStrategy(),
        "consensus": ConsensusStrategy(),
        "elastic": ElasticStrategy(),
        "mcts": MCTSStrategy(),
    }

    @classmethod
    def get_strategy(cls, mode: str) -> EnsembleStrategy:
        mode = (mode or "consensus").lower().strip()
        return cls._strategies.get(mode, cls._strategies["consensus"])

