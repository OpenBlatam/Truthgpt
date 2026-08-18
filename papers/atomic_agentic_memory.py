"""
AtomMem - Learnable Dynamic Agentic Memory with Atomic Memory Operations
========================================================================
Based on "AtomMem: Learnable Dynamic Agentic Memory with Atomic Memory
Operation" (arXiv:2601.08323v2, Jan 2026)

Key idea:
---------
Decomposes memory management into atomic CRUD operations (ADD, UPDATE, DELETE, NOOP)
chosen per observation by a similarity-driven policy, keeping memory fresh and compact.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import AtomicMemoryConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class AtomicAgenticMemory(BasePaperModule):
    """
    Maintains a compact agent memory via atomic CRUD operations chosen per
    incoming observation by a similarity-driven policy.
    """

    metadata = PaperMetadata(
        paper_id="atomic_agentic_memory",
        paper_name="AtomMem: Learnable Dynamic Agentic Memory with Atomic Memory Operation",
        category=PaperCategory.MULTI_AGENT_MEMORY,
        arxiv_id="2601.08323v2",
        year=2026,
        authors=["AtomMem Authors"],
        key_techniques=["Atomic Operations", "ADD UPDATE DELETE NOOP", "Operation Log Replay"],
        speedup=1.6,
        description="Decomposes agent memory management into atomic CRUD operations to prevent context bloat.",
        scholar_query="AtomMem Learnable Dynamic Agentic Memory Atomic Memory Operation",
    )

    def __init__(
        self,
        dup_threshold: float = 0.85,
        update_threshold: float = 0.45,
        config: Optional[AtomicMemoryConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = AtomicMemoryConfig(
                dup_threshold=dup_threshold,
                update_threshold=update_threshold,
            )
            self.config.validate()

        self.dup_threshold = self.config.dup_threshold
        self.update_threshold = self.config.update_threshold
        self.max_entries = self.config.max_entries
        self._store: List[Dict[str, Any]] = []
        self._log: List[Dict[str, Any]] = []
        self._next_id = 0

    @staticmethod
    def _vectorize(text: str) -> Dict[str, int]:
        """Convert input string into bag-of-words token frequency vector."""
        vec: Dict[str, int] = {}
        if not text:
            return vec
        for tok in _TOKEN_RE.findall(str(text).lower()):
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    @classmethod
    def _cosine(cls, a: Dict[str, int], b: Dict[str, int]) -> float:
        """Compute cosine similarity between two word frequency vectors."""
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def _best_match(self, vec: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Find the item in memory store with highest cosine similarity to input vec."""
        best, best_sim = None, 0.0
        for item in self._store:
            sim = self._cosine(vec, item["_vec"])
            if sim > best_sim:
                best, best_sim = item, sim
        if best is not None:
            return {**best, "_sim": best_sim}
        return None

    def decide_op(self, observation: str) -> PaperResult:
        """
        Pick the atomic operation for an observation without mutating memory state.
        """
        if not isinstance(observation, str):
            observation = str(observation or "")

        vec = self._vectorize(observation)
        match = self._best_match(vec)
        if match is None:
            return PaperResult({"op": "ADD", "target_id": None, "similarity": 0.0})

        sim = match["_sim"]
        if sim >= self.dup_threshold:
            op = "NOOP"
        elif sim >= self.update_threshold:
            op = "UPDATE"
        else:
            op = "ADD"

        return PaperResult({"op": op, "target_id": match["id"], "similarity": round(sim, 4)})

    def ingest(self, observation: str) -> PaperResult:
        """
        Decide and apply the atomic operation for one observation.
        """
        if not isinstance(observation, str):
            observation = str(observation or "")

        decision = self.decide_op(observation)
        op = decision["op"]
        vec = self._vectorize(observation)

        if op == "ADD":
            item = {"id": self._next_id, "content": observation, "_vec": vec, "hits": 1}
            self._store.append(item)
            self._next_id += 1
            decision["target_id"] = item["id"]

            if self.max_entries and len(self._store) > self.max_entries:
                min_idx = min(range(len(self._store)), key=lambda i: self._store[i]["hits"])
                evicted = self._store.pop(min_idx)
                self._log.append({"op": "DELETE", "target_id": evicted["id"], "similarity": 0.0, "reason": "capacity"})
        elif op == "UPDATE":
            for item in self._store:
                if item["id"] == decision["target_id"]:
                    if len(observation) > len(item["content"]):
                        item["content"] = observation
                    for t, c in vec.items():
                        item["_vec"][t] = item["_vec"].get(t, 0) + c
                    item["hits"] += 1
                    break

        self._log.append(decision.to_dict() if isinstance(decision, PaperResult) else decision)
        return decision

    def process(self, observations: List[str]) -> PaperResult:
        """
        Ingest a batch of observations and report the operation profile.
        """
        if observations is None:
            observations = []

        counts = {"ADD": 0, "UPDATE": 0, "DELETE": 0, "NOOP": 0}
        for obs in observations:
            res = self.ingest(obs)
            counts[res["op"]] += 1

        ingested = len(observations)
        retained = len(self._store)
        compression = round(1.0 - (retained / ingested), 4) if ingested > 0 else 0.0

        return PaperResult({
            "op_counts": counts,
            "observations_ingested": ingested,
            "memory_size": retained,
            "compression_ratio": compression,
            "redundancy_dropped": counts["NOOP"],
        })

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search memory store for entries matching query by cosine similarity.
        """
        if not query or not self._store:
            return []

        q_vec = self._vectorize(query)
        scored = []
        for item in self._store:
            sim = self._cosine(q_vec, item["_vec"])
            scored.append({"id": item["id"], "content": item["content"], "hits": item["hits"], "similarity": round(sim, 4)})

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[: max(1, top_k)]

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return clean snapshot of current memory contents."""
        return [{"id": i["id"], "content": i["content"], "hits": i["hits"]} for i in self._store]

    def reset(self) -> None:
        """Reset memory store and operation log to empty initial state."""
        self._store.clear()
        self._log.clear()
        self._next_id = 0

    def execute(
        self,
        observations: Optional[List[str]] = None,
        observation: Optional[str] = None,
        **kwargs: Any,
    ) -> PaperResult:
        """Execute atomic memory operations."""
        if observation is not None:
            return self.ingest(observation)
        obs_list = observations if observations is not None else kwargs.get(
            "observations",
            [
                "User requested sales report for Q1 2026",
                "User requested sales report for Q1 2026 in PDF format",
                "Server responded with status code 200",
                "Database backup completed at midnight",
            ],
        )
        return self.process(obs_list)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "dup_threshold": self.dup_threshold,
            "update_threshold": self.update_threshold,
            "memory_size": len(self._store),
            "log_entries": len(self._log),
        }


__all__ = ["AtomicAgenticMemory"]
