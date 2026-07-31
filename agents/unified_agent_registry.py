"""Unified Agent Registry module for Optimization Core.

Provides centralized agent registration, lookup, instantiations, and lifecycle management
for all agent implementations across the platform.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Type
from optimization_core.agents.framework.architectures.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Thread-safe registry for agent implementations and active instances."""

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._classes: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self._registry_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """Return global AgentRegistry singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_class(self, name: str, agent_cls: Type[BaseAgent]) -> None:
        """Register an agent implementation class by name."""
        with self._registry_lock:
            self._classes[name] = agent_cls
            logger.info("AgentRegistry: registered agent class '%s'", name)

    def register_instance(self, name: str, agent_instance: BaseAgent) -> None:
        """Register an active agent instance by name."""
        with self._registry_lock:
            self._instances[name] = agent_instance
            logger.info("AgentRegistry: registered agent instance '%s'", name)

    def get_class(self, name: str) -> Optional[Type[BaseAgent]]:
        """Retrieve registered agent class by name."""
        with self._registry_lock:
            return self._classes.get(name)

    def get_instance_by_name(self, name: str) -> Optional[BaseAgent]:
        """Retrieve active agent instance by name."""
        with self._registry_lock:
            return self._instances.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent class names."""
        with self._registry_lock:
            return list(self._classes.keys())

    def list_active_instances(self) -> List[str]:
        """List all active agent instance names."""
        with self._registry_lock:
            return list(self._instances.keys())

    def create(self, agent_type: str, name: str, role: str, **kwargs: Any) -> BaseAgent:
        """Instantiate, register, and return a new agent of type `agent_type`."""
        agent_cls = self.get_class(agent_type)
        if agent_cls is None:
            raise KeyError(f"Agent type '{agent_type}' is not registered in AgentRegistry.")
        instance = agent_cls(name=name, role=role, **kwargs)
        self.register_instance(name, instance)
        return instance


__all__ = ["AgentRegistry"]
