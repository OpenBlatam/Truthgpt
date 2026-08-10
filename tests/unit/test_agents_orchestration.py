"""
Unit tests for optimization_core.agents.orchestration re-exports and primitives.
"""

import pytest
from optimization_core.agents.orchestration import (
    SwarmOrchestrator,
    GraphOrchestrator,
    PlanningAgent,
    AgentComposer,
    AgentEnsemble,
    SmartScheduler,
    AgentScheduler,
)


def test_orchestration_exports():
    assert SwarmOrchestrator is not None
    assert GraphOrchestrator is not None
    assert PlanningAgent is not None
    assert AgentComposer is not None
    assert AgentEnsemble is not None
    assert SmartScheduler is not None
    assert AgentScheduler is not None


def test_swarm_orchestrator_instantiation():
    orchestrator = SwarmOrchestrator()
    assert orchestrator is not None


def test_agent_composer_instantiation():
    composer = AgentComposer()
    assert composer is not None


def test_agent_ensemble_instantiation():
    ensemble = AgentEnsemble()
    assert ensemble is not None
