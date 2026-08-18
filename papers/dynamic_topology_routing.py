"""
DyTopo - Dynamic Topology Routing for Multi-Agent Reasoning via Semantic Matching
=================================================================================
Based on "DyTopo: Dynamic Topology Routing for Multi-Agent Reasoning via
Semantic Matching" (arXiv:2602.06039v1, Feb 2026)

Key idea:
---------
Rewires the multi-agent graph at every reasoning round based on semantic matching
between the active message and agent capabilities, pruning irrelevant edges.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import DynamicTopologyConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class DynamicTopologyRouter(BasePaperModule):
    """
    Rewires a multi-agent communication graph each reasoning round using semantic
    matching between the active message and each agent's capabilities.
    """

    metadata = PaperMetadata(
        paper_id="dynamic_topology_routing",
        paper_name="DyTopo: Dynamic Topology Routing for Multi-Agent Reasoning via Semantic Matching",
        category=PaperCategory.MULTI_AGENT,
        arxiv_id="2602.06039v1",
        year=2026,
        authors=["DyTopo Authors"],
        key_techniques=["Semantic Agent Matching", "Dynamic Graph Rewiring", "Message Pruning"],
        speedup=2.0,
        description="Rewires multi-agent graphs dynamically per reasoning round based on relevance.",
        scholar_query="DyTopo Dynamic Topology Routing Multi-Agent Reasoning Semantic Matching",
    )

    def __init__(
        self,
        top_k: int = 2,
        relevance_threshold: float = 0.05,
        config: Optional[DynamicTopologyConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = DynamicTopologyConfig(
                top_k=max(1, top_k),
                relevance_threshold=relevance_threshold,
            )
            self.config.validate()

        self.top_k = max(1, self.config.top_k)
        self.relevance_threshold = self.config.relevance_threshold

    @staticmethod
    def _vectorize(text: str) -> Dict[str, int]:
        """Convert input string into token count dictionary."""
        vec: Dict[str, int] = {}
        if not text:
            return vec
        for tok in _TOKEN_RE.findall(str(text).lower()):
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    @classmethod
    def _cosine(cls, a: Dict[str, int], b: Dict[str, int]) -> float:
        """Compute cosine similarity between two frequency vectors."""
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

    def route_round(self, message: str, agents: List[Dict[str, str]]) -> PaperResult:
        """
        Score agents against the current message and build a sparse topology.
        """
        if not agents:
            return PaperResult({"active_agents": [], "edges": [], "density": 0.0, "edges_saved": 0})

        msg_vec = self._vectorize(message or "")
        scored = [
            (
                a.get("name", f"agent_{i}"),
                self._cosine(msg_vec, self._vectorize(a.get("capabilities", ""))),
                a,
            )
            for i, a in enumerate(agents)
        ]

        active = [s for s in scored if s[1] >= self.relevance_threshold]
        if not active:
            active = [max(scored, key=lambda s: s[1])]

        names = [s[0] for s in active]
        caps = {s[0]: self._vectorize(s[2].get("capabilities", "")) for s in active}

        # Rewire: each active agent links to its top_k most semantically similar peers
        edges: List[Tuple[str, str, float]] = []
        for src in names:
            peers = sorted(
                ((dst, self._cosine(caps[src], caps[dst])) for dst in names if dst != src),
                key=lambda p: p[1],
                reverse=True,
            )
            for dst, sim in peers[: self.top_k]:
                edges.append((src, dst, round(sim, 4)))

        n = len(names)
        full_mesh = n * (n - 1)
        edges_saved = max(0, full_mesh - len(edges))
        density = round(len(edges) / full_mesh, 4) if full_mesh > 0 else 0.0

        return PaperResult({
            "active_agents": names,
            "relevance": {s[0]: round(s[1], 4) for s in scored},
            "edges": edges,
            "num_active": n,
            "num_pruned": len(agents) - n,
            "density": density,
            "edges_saved": edges_saved,
            "full_mesh_edges": full_mesh,
        })

    def run(self, query: str, agents: List[Dict[str, str]], rounds: int = 3) -> PaperResult:
        """
        Simulate multi-round reasoning, re-routing the topology each round.
        """
        num_rounds = max(1, rounds)
        history = [self.route_round(query, agents) for _ in range(num_rounds)]
        total_edges = sum(r["edges_saved"] for r in history)
        avg_density = round(sum(r["density"] for r in history) / len(history), 4) if history else 0.0

        return PaperResult({
            "rounds": len(history),
            "avg_density": avg_density,
            "total_edges_saved": total_edges,
            "last_topology": history[-1] if history else {},
        })

    def execute(
        self,
        query: Optional[str] = None,
        message: Optional[str] = None,
        agents: Optional[List[Dict[str, str]]] = None,
        rounds: int = 3,
        **kwargs: Any,
    ) -> PaperResult:
        """Execute dynamic topology routing simulation."""
        target_msg = query or message or kwargs.get("message", "Optimize CUDA memory cache for large tensor matrix multiplication")
        target_agents = agents if agents is not None else kwargs.get(
            "agents",
            [
                {"name": "gpu_expert", "capabilities": "cuda memory tensor matrix gpu kernel"},
                {"name": "math_solver", "capabilities": "equations algebra calculus logic proof"},
                {"name": "web_searcher", "capabilities": "crawler search engine browser web api"},
                {"name": "code_refactorer", "capabilities": "python rust julia code formatting ast"},
            ],
        )
        r = kwargs.get("rounds", rounds)
        return self.run(target_msg, target_agents, rounds=r)

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "top_k": self.top_k,
            "relevance_threshold": self.relevance_threshold,
        }


__all__ = ["DynamicTopologyRouter"]
