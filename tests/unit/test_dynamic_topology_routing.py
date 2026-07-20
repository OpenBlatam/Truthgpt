"""Unit tests for DyTopo dynamic multi-agent topology routing (arXiv:2602.06039v1).

Covers the paper's core promise: re-route the agent graph each round via semantic
matching so only relevant agents are connected, pruning the rest and saving edges
versus a static full mesh.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from papers.dynamic_topology_routing import DynamicTopologyRouter  # noqa: E402
from latency_optimizations import apply_dynamic_topology_routing  # noqa: E402


def _agents() -> list[dict]:
    return [
        {"name": "planner", "capabilities": "plan decompose strategy schedule task"},
        {"name": "coder", "capabilities": "code implement python function debug"},
        {"name": "researcher", "capabilities": "search retrieve web evidence cite"},
        {"name": "critic", "capabilities": "verify review correctness evaluate"},
    ]


def test_empty_agents_is_safe():
    """No agents -> empty, well-formed topology (no crash, no edges)."""
    r = DynamicTopologyRouter().route_round("anything", [])
    assert r == {"active_agents": [], "edges": [], "density": 0.0, "edges_saved": 0}


def test_relevant_query_activates_matching_agents():
    """A query spanning every capability should activate all agents and prune none."""
    topo = DynamicTopologyRouter(top_k=2).route_round(
        "plan and code a fix, then search evidence and verify correctness", _agents()
    )
    assert set(topo["active_agents"]) == {"planner", "coder", "researcher", "critic"}
    assert topo["num_pruned"] == 0


def test_narrow_query_prunes_irrelevant_agents():
    """A query touching one capability prunes the rest (semantic routing, not full mesh)."""
    topo = DynamicTopologyRouter(top_k=2).route_round("verify review correctness", _agents())
    assert "critic" in topo["active_agents"]
    assert topo["num_pruned"] >= 1
    assert topo["num_active"] + topo["num_pruned"] == len(_agents())


def test_topology_is_sparser_than_full_mesh():
    """With top_k below n-1, the rewired graph keeps fewer edges than a full mesh."""
    topo = DynamicTopologyRouter(top_k=1).route_round(
        "plan and code a fix, then search evidence and verify correctness", _agents()
    )
    n = topo["num_active"]
    assert len(topo["edges"]) == n * 1  # top_k outgoing edges per active node
    assert topo["edges_saved"] == topo["full_mesh_edges"] - len(topo["edges"])
    assert 0.0 <= topo["density"] <= 1.0


def test_top_k_bounds_out_degree():
    """Each active agent emits at most top_k edges regardless of peer count."""
    top_k = 2
    topo = DynamicTopologyRouter(top_k=top_k).route_round(
        "plan and code a fix, then search evidence and verify correctness", _agents()
    )
    out_degree: dict[str, int] = {}
    for src, _dst, _sim in topo["edges"]:
        out_degree[src] = out_degree.get(src, 0) + 1
    assert all(d <= top_k for d in out_degree.values())


def test_never_stalls_when_nothing_matches():
    """If no agent clears the threshold, the single most relevant one stays active."""
    topo = DynamicTopologyRouter().route_round("xyzzy nonsense token", _agents())
    assert topo["num_active"] == 1


def test_top_k_floor_is_one():
    """top_k is clamped to a minimum of 1 even if caller passes 0 or negative."""
    assert DynamicTopologyRouter(top_k=0).top_k == 1


def test_run_aggregates_rounds_and_matches_wrapper():
    """run() reports per-round aggregates; the apply_* wrapper mirrors run()."""
    query = "plan and code a fix, then search evidence and verify correctness"
    direct = DynamicTopologyRouter(top_k=2).run(query, _agents(), rounds=3)
    assert direct["rounds"] == 3
    # 3 identical rounds -> total saved is 3x a single round's saving.
    single = DynamicTopologyRouter(top_k=2).route_round(query, _agents())
    assert direct["total_edges_saved"] == 3 * single["edges_saved"]

    wrapped = apply_dynamic_topology_routing(query, _agents(), top_k=2, rounds=3)
    assert wrapped["total_edges_saved"] == direct["total_edges_saved"]
    assert wrapped["avg_density"] == direct["avg_density"]
