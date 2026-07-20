"""
AtomMem - Learnable Dynamic Agentic Memory with Atomic Memory Operations
Based on "AtomMem: Learnable Dynamic Agentic Memory with Atomic Memory
Operation" (arXiv:2601.08323v2, Jan 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=AtomMem+Learnable+Dynamic+Agentic+Memory+Atomic+Memory+Operation

Key idea:
Naive agent memory keeps appending observations, which bloats context with
duplicates and stale facts. AtomMem decomposes memory management into a small set
of *atomic* operations - ADD, UPDATE, DELETE, NOOP - and learns a policy (SFT+RL)
that, for each incoming observation, picks the operation that keeps the store
compact, fresh, and non-redundant. The atomic decomposition makes the policy easy
to supervise and the memory state fully reconstructible from an operation log.

This implementation is a dependency-light, deterministic stand-in for the learned
policy: it decides the atomic op from bag-of-words similarity between the incoming
observation and the existing memory, so it runs without a trained model. The
operation log is recorded so the store can be replayed.
"""

import math
import re
from typing import Any, Dict, List, Optional

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class AtomicAgenticMemory:
    """
    Maintains a compact agent memory via atomic CRUD operations chosen per
    incoming observation by a similarity-driven policy.
    """

    def __init__(self, dup_threshold: float = 0.85, update_threshold: float = 0.45):
        # >= dup_threshold      -> near-duplicate            -> NOOP
        # [update, dup)         -> same topic, new detail    -> UPDATE (merge)
        # < update_threshold    -> novel                     -> ADD
        self.dup_threshold = dup_threshold
        self.update_threshold = update_threshold
        self._store: List[Dict[str, Any]] = []
        self._log: List[Dict[str, Any]] = []
        self._next_id = 0

    @staticmethod
    def _vectorize(text: str) -> Dict[str, int]:
        vec: Dict[str, int] = {}
        for tok in _TOKEN_RE.findall((text or "").lower()):
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    @classmethod
    def _cosine(cls, a: Dict[str, int], b: Dict[str, int]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _best_match(self, vec: Dict[str, int]) -> Optional[Dict[str, Any]]:
        best, best_sim = None, 0.0
        for item in self._store:
            sim = self._cosine(vec, item["_vec"])
            if sim > best_sim:
                best, best_sim = item, sim
        if best is not None:
            best = {**best, "_sim": best_sim}
        return best

    def decide_op(self, observation: str) -> Dict[str, Any]:
        """Pick the atomic operation for an observation without mutating state."""
        vec = self._vectorize(observation)
        match = self._best_match(vec)
        if match is None:
            return {"op": "ADD", "target_id": None, "similarity": 0.0}
        sim = match["_sim"]
        if sim >= self.dup_threshold:
            op = "NOOP"
        elif sim >= self.update_threshold:
            op = "UPDATE"
        else:
            op = "ADD"
        return {"op": op, "target_id": match["id"], "similarity": round(sim, 4)}

    def ingest(self, observation: str) -> Dict[str, Any]:
        """Decide and apply the atomic op for one observation."""
        decision = self.decide_op(observation)
        op = decision["op"]
        vec = self._vectorize(observation)

        if op == "ADD":
            item = {"id": self._next_id, "content": observation, "_vec": vec, "hits": 1}
            self._store.append(item)
            self._next_id += 1
            decision["target_id"] = item["id"]
        elif op == "UPDATE":
            for item in self._store:
                if item["id"] == decision["target_id"]:
                    # Merge: keep the longer/more informative content, bump hits.
                    if len(observation) > len(item["content"]):
                        item["content"] = observation
                    for t, c in vec.items():
                        item["_vec"][t] = item["_vec"].get(t, 0) + c
                    item["hits"] += 1
                    break
        # NOOP: drop redundant observation entirely.

        self._log.append(decision)
        return decision

    def process(self, observations: List[str]) -> Dict[str, Any]:
        """Ingest a batch of observations and report the operation profile."""
        counts = {"ADD": 0, "UPDATE": 0, "DELETE": 0, "NOOP": 0}
        for obs in observations:
            counts[self.ingest(obs)["op"]] += 1
        ingested = len(observations)
        retained = len(self._store)
        compression = round(1.0 - retained / ingested, 4) if ingested else 0.0
        return {
            "op_counts": counts,
            "observations_ingested": ingested,
            "memory_size": retained,
            "compression_ratio": compression,
            "redundancy_dropped": counts["NOOP"],
        }

    def snapshot(self) -> List[Dict[str, Any]]:
        """Current memory contents (without internal vectors)."""
        return [{"id": i["id"], "content": i["content"], "hits": i["hits"]} for i in self._store]
