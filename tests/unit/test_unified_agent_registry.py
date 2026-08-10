"""
Unit tests for optimization_core.agents.unified_agent_registry.
"""

import pytest
from optimization_core.agents.unified_agent_registry import AgentRegistry, agent_registry
from optimization_core.agents.framework.architectures.base_agent import BaseAgent
from optimization_core.agents.framework.exceptions import RegistryError


class DummyAgent(BaseAgent):
    """Dummy agent implementation for registry testing."""
    async def process(self, query: str, context: None = None):
        return {"result": f"processed: {query}"}


def test_agent_registry_singleton():
    reg1 = AgentRegistry.get_instance()
    reg2 = AgentRegistry.get_instance()
    assert reg1 is reg2
    assert agent_registry is reg1


def test_register_and_get_class():
    registry = AgentRegistry()
    registry.register_class("dummy", DummyAgent)
    assert registry.get_class("dummy") is DummyAgent
    assert "dummy" in registry.list_agents()


def test_unregister_class():
    registry = AgentRegistry()
    registry.register_class("dummy", DummyAgent)
    assert registry.unregister_class("dummy") is True
    assert registry.get_class("dummy") is None
    assert registry.unregister_class("nonexistent") is False


def test_register_and_get_instance():
    registry = AgentRegistry()
    agent = DummyAgent(name="test_agent", role="tester")
    registry.register_instance("test_agent", agent)
    assert registry.get_instance_by_name("test_agent") is agent
    assert "test_agent" in registry.list_active_instances()


def test_create_agent():
    registry = AgentRegistry()
    registry.register_class("dummy", DummyAgent)
    instance = registry.create("dummy", name="created_agent", role="worker")
    assert isinstance(instance, DummyAgent)
    assert instance.name == "created_agent"
    assert registry.get_instance_by_name("created_agent") is instance


def test_create_unregistered_agent_raises():
    registry = AgentRegistry()
    with pytest.raises(RegistryError):
        registry.create("unknown_type", name="fail", role="fail")


def test_register_defaults():
    registry = AgentRegistry()
    registry.register_defaults()
    agents = registry.list_agents()
    assert "code_interpreter" in agents
    assert "data_analysis" in agents
    assert "embodied_rl" in agents
