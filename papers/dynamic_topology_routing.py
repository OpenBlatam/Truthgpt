"""
DyTopo - Dynamic Topology Routing for Multi-Agent Reasoning via Semantic Matching
Based on "DyTopo: Dynamic Topology Routing for Multi-Agent Reasoning via
Semantic Matching" (arXiv:2602.06039v1, Feb 2026)

Source (Google Scholar): https://scholar.google.com/scholar?q=DyTopo+Dynamic+Topology+Routing+Multi-Agent+Reasoning+Semantic+Matching

Key idea:
Most multi-agent systems use a *static* communication topology (full mesh, star,
chain) fixed before reasoning starts. DyTopo instead rewires the agent graph at
*every* reasoning round: it scores how relevant each agent is to the current
message via semantic matching and connects only the most relevant agents,
pruning the rest. This cuts message passing (and tokens/cost) versus a full mesh
while routing information to the agents that can actually advance the reasoning.

This implementation is a dependency-light, deterministic stand-in for the paper's
learned semantic matcher: it scores relevance with bag-of-words cosine similarity
over each agent's capability description, so it runs without an embedding model.
"""

import math
import re
from typing import Any, Dict, List, Tuple

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class DynamicTopologyRouter:
    """
    Rewires a multi-agent communication graph each reasoning round using semantic
    matching between the active message and each agent's capabilities.
    """

    def __init__(self, top_k: int = 2, relevance_threshold: float = 0.05):
        # top_k: max outgoing edges kept per active agent (sparsity control).
        self.top_k = max(1, top_k)
        self.relevance_threshold = relevance_threshold

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

    def route_round(self, message: str, agents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Score agents against the current message and build a sparse topology.

        agents: list of {"name": str, "capabilities": str}.
        Returns the active agents, the rewired (directed) edges, and the density
        savings versus a full mesh.
        """
        if not agents:
            return {"active_agents": [], "edges": [], "density": 0.0, "edges_saved": 0}

        msg_vec = self._vectorize(message)
        scored = [
            (a.get("name", f"agent_{i}"), self._cosine(msg_vec, self._vectorize(a.get("capabilities", ""))), a)
            for i, a in enumerate(agents)
        ]
        # Activate agents whose relevance clears the threshold; always keep the
        # single most relevant agent so the round never stalls.
        active = [s for s in scored if s[1] >= self.relevance_threshold]
        if not active:
            active = [max(scored, key=lambda s: s[1])]

        names = [s[0] for s in active]
        caps = {s[0]: self._vectorize(s[2].get("capabilities", "")) for s in active}

        # Rewire: each active agent links to its top_k most semantically similar peers.
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
        full_mesh = n * (n - 1)  # directed full mesh
        edges_saved = max(0, full_mesh - len(edges))
        density = round(len(edges) / full_mesh, 4) if full_mesh else 0.0

        return {
            "active_agents": names,
            "relevance": {s[0]: round(s[1], 4) for s in scored},
            "edges": edges,
            "num_active": n,
            "num_pruned": len(agents) - n,
            "density": density,
            "edges_saved": edges_saved,
            "full_mesh_edges": full_mesh,
        }

    def run(self, query: str, agents: List[Dict[str, str]], rounds: int = 3) -> Dict[str, Any]:
        """Simulate multi-round reasoning, re-routing the topology each round."""
        history = [self.route_round(query, agents) for _ in range(max(1, rounds))]
        total_edges = sum(r["edges_saved"] for r in history)
        avg_density = round(sum(r["density"] for r in history) / len(history), 4)
        return {
            "rounds": len(history),
            "avg_density": avg_density,
            "total_edges_saved": total_edges,
            "last_topology": history[-1],
        }
