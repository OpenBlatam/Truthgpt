"""
🐝 TruthGPT Cloud - Multi-Agent Swarm Graph Topology & Dependency Engine
Formalizes multi-agent coordination architectures using NetworkX directed graphs (DiGraph).
Provides topological reasoning sort, cycle/deadlock detection, centrality analysis, and DAG validation.
"""

from typing import List, Dict, Any

_HAS_NETWORKX = False
try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    _HAS_NETWORKX = False


def build_swarm_topology_graph(
    agents: List[Any],
    topology_type: str = "hierarchical",
) -> Any:
    """
    Construct a NetworkX DiGraph representing agent communication channels and dependencies.

    Args:
        agents: List of SwarmAgentNode objects or dictionaries.
        topology_type: 'hierarchical', 'peer_to_peer', 'star', 'adversarial', or 'ring'.

    Returns:
        nx.DiGraph instance or fallback dict if networkx is unavailable.
    """
    if not _HAS_NETWORKX:
        # Fallback in-process representation
        node_ids = [
            getattr(a, "agent_id", None) or (a.get("agent_id") if isinstance(a, dict) else str(a))
            for a in agents
        ]
        return {
            "is_fallback": True,
            "nodes": node_ids,
            "topology_type": topology_type,
            "edges": [(node_ids[i], node_ids[i + 1]) for i in range(len(node_ids) - 1)] if len(node_ids) > 1 else [],
        }

    G = nx.DiGraph()

    # 1. Add nodes with rich agent metadata
    for a in agents:
        if isinstance(a, dict):
            aid = a.get("agent_id", "unknown")
            role = a.get("role_name", "")
            expertise = a.get("domain_expertise", "")
            rigor = a.get("rigor_level", 2)
        else:
            aid = getattr(a, "agent_id", "unknown")
            role = getattr(a, "role_name", "")
            expertise = getattr(a, "domain_expertise", "")
            rigor = getattr(a, "rigor_level", 2)

        G.add_node(aid, role_name=role, domain_expertise=expertise, rigor_level=rigor)

    node_ids = list(G.nodes)
    n = len(node_ids)
    if n <= 1:
        return G

    # 2. Add edges based on canonical swarm topology
    top_lower = topology_type.lower()

    if "hierarchical" in top_lower or "dag" in top_lower:
        # Master coordinator (index 0) feeds domain agents (indices 1 to n-2),
        # which feed synthesis/verification final agent (index n-1)
        root = node_ids[0]
        sink = node_ids[-1] if n > 2 else None

        if n == 2:
            G.add_edge(node_ids[0], node_ids[1], relation="delegates_to")
        else:
            for intermediate in node_ids[1:-1]:
                G.add_edge(root, intermediate, relation="delegates_to")
                if sink:
                    G.add_edge(intermediate, sink, relation="submits_proof_to")

    elif "peer_to_peer" in top_lower or "mesh" in top_lower:
        # Full bidirectional mesh between all agents
        for i in range(n):
            for j in range(i + 1, n):
                G.add_edge(node_ids[i], node_ids[j], relation="peer_dialogue")
                G.add_edge(node_ids[j], node_ids[i], relation="peer_dialogue")

    elif "star" in top_lower:
        # Central coordinator connected bidirectionally to all workers
        hub = node_ids[0]
        for worker in node_ids[1:]:
            G.add_edge(hub, worker, relation="dispatches")
            G.add_edge(worker, hub, relation="reports_back")

    elif "adversarial" in top_lower or "debate" in top_lower:
        # Red Team vs Blue Team:
        # Proponents (even indices) attack/critique adversaries (odd indices)
        # All feed consensus arbitrator (last node)
        arbitrator = node_ids[-1]
        for i in range(n - 1):
            target = (i + 1) % (n - 1)
            G.add_edge(node_ids[i], node_ids[target], relation="adversarial_critique")
            G.add_edge(node_ids[i], arbitrator, relation="proposes_concession")

    elif "ring" in top_lower:
        # Pipeline ring
        for i in range(n):
            nxt = (i + 1) % n
            G.add_edge(node_ids[i], node_ids[nxt], relation="passes_token")

    else:
        # Default linear pipeline
        for i in range(n - 1):
            G.add_edge(node_ids[i], node_ids[i + 1], relation="pipeline_step")

    return G


def get_topological_reasoning_order(graph: Any) -> List[str]:
    """
    Compute sequential topological execution order of agents for acyclic reasoning DAGs.
    If the graph contains cycles, returns a heuristic dependency ordering.
    """
    if not _HAS_NETWORKX or isinstance(graph, dict):
        if isinstance(graph, dict):
            return graph.get("nodes", [])
        return []

    try:
        if nx.is_directed_acyclic_graph(graph):
            return list(nx.topological_sort(graph))
        # If cycles exist (e.g. peer-to-peer or ring), order by in-degree ascending
        return sorted(graph.nodes, key=lambda n: graph.in_degree(n))
    except Exception:
        return list(graph.nodes)


def detect_deadlocks_and_cycles(graph: Any) -> Dict[str, Any]:
    """
    Inspect the swarm graph for cycles that could cause reasoning deadlocks or infinite message loops.
    """
    if not _HAS_NETWORKX or isinstance(graph, dict):
        return {
            "has_networkx": False,
            "is_acyclic": True,
            "simple_cycles_count": 0,
            "cycles": [],
            "has_deadlock_risk": False,
        }

    try:
        is_dag = nx.is_directed_acyclic_graph(graph)
        cycles = list(nx.simple_cycles(graph)) if not is_dag else []
        return {
            "has_networkx": True,
            "is_acyclic": is_dag,
            "simple_cycles_count": len(cycles),
            "cycles": cycles[:10],
            "has_deadlock_risk": len(cycles) > 0,
        }
    except Exception as e:
        return {
            "has_networkx": True,
            "error": str(e),
            "is_acyclic": False,
            "simple_cycles_count": 0,
            "cycles": [],
            "has_deadlock_risk": False,
        }


def calculate_agent_influence(graph: Any) -> Dict[str, float]:
    """
    Calculate degree centrality to measure the influence and connectivity of each agent.
    """
    if not _HAS_NETWORKX or isinstance(graph, dict):
        nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        return {n: 1.0 / max(1, len(nodes)) for n in nodes}

    try:
        centrality = nx.degree_centrality(graph)
        return {k: round(v, 4) for k, v in centrality.items()}
    except Exception:
        return {n: 0.0 for n in graph.nodes}


def get_graph_metrics(graph: Any) -> Dict[str, Any]:
    """
    Summarize structural metrics of the multi-agent graph (density, node/edge counts, diameter).
    """
    if not _HAS_NETWORKX or isinstance(graph, dict):
        nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        edges = graph.get("edges", []) if isinstance(graph, dict) else []
        return {
            "has_networkx": False,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": 0.0,
            "is_dag": True,
            "execution_order": nodes,
        }

    try:
        is_dag = nx.is_directed_acyclic_graph(graph)
        density = round(nx.density(graph), 4)
        order = get_topological_reasoning_order(graph)
        influence = calculate_agent_influence(graph)

        return {
            "has_networkx": True,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": density,
            "is_dag": is_dag,
            "execution_order": order,
            "agent_influence": influence,
            "deadlock_check": detect_deadlocks_and_cycles(graph),
        }
    except Exception as e:
        return {
            "has_networkx": True,
            "error": str(e),
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
        }


# Alias for topological metric retrieval
get_topology_metrics = get_graph_metrics


__all__ = [
    "build_swarm_topology_graph",
    "get_topological_reasoning_order",
    "detect_deadlocks_and_cycles",
    "calculate_agent_influence",
    "get_graph_metrics",
    "get_topology_metrics",
    "_HAS_NETWORKX",
]
