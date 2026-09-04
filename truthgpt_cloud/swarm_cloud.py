"""
🐝 TruthGPT Cloud - Multi-Agent Swarm Compatibility Bridge
Re-exports SwarmAgentNode, SwarmExecutionTrace, and CloudSwarmOrchestrator from truthgpt_cloud.swarm.
"""

from .swarm import (
    SwarmAgentNode,
    DebateRound,
    SwarmExecutionTrace,
    CloudSwarmOrchestrator,
    cloud_swarm,
    get_default_swarm_nodes,
    get_adversarial_team_nodes,
    build_swarm_topology_graph,
    get_topological_reasoning_order,
    detect_deadlocks_and_cycles,
    calculate_agent_influence,
    get_graph_metrics,
    _HAS_NETWORKX,
)

__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "SwarmExecutionTrace",
    "CloudSwarmOrchestrator",
    "cloud_swarm",
    "get_default_swarm_nodes",
    "get_adversarial_team_nodes",
    "build_swarm_topology_graph",
    "get_topological_reasoning_order",
    "detect_deadlocks_and_cycles",
    "calculate_agent_influence",
    "get_graph_metrics",
    "_HAS_NETWORKX",
]
