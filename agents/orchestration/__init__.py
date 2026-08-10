"""
TruthGPT Orchestration Framework.

Provides multi-agent swarm routing, workflow composition, ensemble consensus,
and dynamic agent task scheduling engines.
"""

from __future__ import annotations

from . import composer, ensemble, scheduler, swarm

from .swarm.swarm_orchestrator import SwarmOrchestrator
from .swarm.graph_orchestrator import GraphOrchestrator
from .swarm.planning_agent import PlanningAgent
from .composer.agent_composer import AgentComposer
from .ensemble.ensemble import AgentEnsemble
from .scheduler.smart_scheduler import SmartScheduler
from .scheduler import AgentScheduler

__all__ = [
    # Submodules
    "composer",
    "ensemble",
    "scheduler",
    "swarm",
    # Orchestration Primitives
    "SwarmOrchestrator",
    "GraphOrchestrator",
    "PlanningAgent",
    "AgentComposer",
    "AgentEnsemble",
    "SmartScheduler",
    "AgentScheduler",
]
