"""
Multi-agent swarm package for TruthGPT Cloud.
"""

from .models import (
    SwarmAgentNode,
    DebateRound,
    SwarmExecutionTrace,
)
from .agents import (
    get_default_swarm_nodes,
    get_adversarial_team_nodes,
)
from .orchestrator import (
    CloudSwarmOrchestrator,
    cloud_swarm,
    build_swarm_topology_graph,
    get_topological_reasoning_order,
    detect_deadlocks_and_cycles,
    calculate_agent_influence,
    get_graph_metrics,
    get_topology_metrics,
    _HAS_NETWORKX,
)

__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "get_default_swarm_nodes",
    "get_adversarial_team_nodes",
    "SwarmExecutionTrace",
    "CloudSwarmOrchestrator",
    "cloud_swarm",
    "build_swarm_topology_graph",
    "get_topological_reasoning_order",
    "detect_deadlocks_and_cycles",
    "calculate_agent_influence",
    "get_graph_metrics",
    "get_topology_metrics",
    "_HAS_NETWORKX",
]
