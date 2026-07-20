import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

def parse_agent_json(raw: str) -> Dict[str, Any]:
    """Best-effort parse of an AgentAction JSON payload."""
    if not raw or not str(raw).strip():
        return {"thought": "", "final_answer": ""}
    text = str(raw).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, str):
            data = json.loads(data)
        return data if isinstance(data, dict) else {"thought": text[:500], "final_answer": text}
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {"thought": text[:500], "final_answer": text}


def _extract_thought(data: Dict[str, Any]) -> str:
    return str(
        data.get("thought")
        or data.get("razonamiento")
        or data.get("reasoning")
        or ""
    ).strip()


def _extract_final(data: Dict[str, Any]) -> str:
    return str(
        data.get("final_answer")
        or data.get("respuesta_final")
        or data.get("answer")
        or ""
    ).strip()


def _extract_confidence(data: Dict[str, Any]) -> float:
    for key in ("confidence", "score", "certainty"):
        if key in data:
            try:
                return max(0.0, min(1.0, float(data[key])))
            except (TypeError, ValueError):
                pass
    meta = data.get("metadata")
    if isinstance(meta, dict):
        for key in ("confidence", "score", "certainty"):
            if key in meta:
                try:
                    return max(0.0, min(1.0, float(meta[key])))
                except (TypeError, ValueError):
                    pass
    return 0.5


def _normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())[:500]


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalize_for_compare(a), _normalize_for_compare(b)).ratio()


def _cluster_by_similarity(
    items: List[Tuple[str, str]],
    threshold: float = 0.55,
) -> List[List[Tuple[str, str]]]:
    """Group (engine_key, final_answer) by textual similarity."""
    clusters: List[List[Tuple[str, str]]] = []
    for key, final in items:
        placed = False
        for cluster in clusters:
            if _similarity(final, cluster[0][1]) >= threshold:
                cluster.append((key, final))
                placed = True
                break
        if not placed:
            clusters.append([(key, final)])
    return clusters


def _pick_largest_cluster(clustered: List[List[Tuple[str, str]]]) -> Tuple[str, str]:
    best = max(clustered, key=len)
    key, final = max(best, key=lambda x: len(x[1]))
    return key, final
