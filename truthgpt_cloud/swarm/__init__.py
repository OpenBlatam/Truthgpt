"""
Multi-agent swarm package for TruthGPT Cloud.
"""

from .agents import (
    SwarmAgentNode,
    DebateRound,
    get_default_swarm_nodes,
    get_adversarial_team_nodes,
)

from .orchestrator import (
    SwarmExecutionTrace,
    CloudSwarmOrchestrator,
    cloud_swarm,
)

__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "get_default_swarm_nodes",
    "get_adversarial_team_nodes",
    "SwarmExecutionTrace",
    "CloudSwarmOrchestrator",
    "cloud_swarm",
]
