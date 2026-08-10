"""Unified Agent Registry module for Optimization Core.

Provides centralized agent registration, lookup, instantiations, and lifecycle management
for all agent implementations across the platform.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple, Type, Union

try:
    from optimization_core.agents.framework.architectures.base_agent import BaseAgent
except ImportError:
    from agents.framework.architectures.base_agent import BaseAgent

try:
    from optimization_core.agents.framework.exceptions import RegistryError
except ImportError:
    RegistryError = KeyError

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Thread-safe registry for agent implementations and active instances."""

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._classes: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self._registry_lock = threading.Lock()
        self._defaults_registered = False

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

    def unregister_class(self, name: str) -> bool:
        """Unregister an agent implementation class by name."""
        with self._registry_lock:
            if name in self._classes:
                del self._classes[name]
                logger.info("AgentRegistry: unregistered agent class '%s'", name)
                return True
            return False

    def has_class(self, name: str) -> bool:
        """Check if an agent class with the given name is registered."""
        return self.get_class(name) is not None

    def register_instance(self, name: str, agent_instance: BaseAgent) -> None:
        """Register an active agent instance by name."""
        with self._registry_lock:
            self._instances[name] = agent_instance
            logger.info("AgentRegistry: registered agent instance '%s'", name)

    def unregister_instance(self, name: str) -> bool:
        """Unregister an active agent instance by name."""
        with self._registry_lock:
            if name in self._instances:
                del self._instances[name]
                logger.info("AgentRegistry: unregistered agent instance '%s'", name)
                return True
            return False

    def has_instance(self, name: str) -> bool:
        """Check if an active agent instance with the given name is registered."""
        with self._registry_lock:
            return name in self._instances

    def get_class(self, name: str) -> Optional[Type[BaseAgent]]:
        """Retrieve registered agent class by name."""
        with self._registry_lock:
            if name not in self._classes and not self._defaults_registered:
                self._register_defaults_unlocked()
            return self._classes.get(name)

    def get_instance_by_name(self, name: str) -> Optional[BaseAgent]:
        """Retrieve active agent instance by name."""
        with self._registry_lock:
            return self._instances.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent class names."""
        with self._registry_lock:
            if not self._defaults_registered:
                self._register_defaults_unlocked()
            return list(self._classes.keys())

    def list_active_instances(self) -> List[str]:
        """List all active agent instance names."""
        with self._registry_lock:
            return list(self._instances.keys())

    def clear(self) -> None:
        """Clear all registered classes and instances."""
        with self._registry_lock:
            self._classes.clear()
            self._instances.clear()
            self._defaults_registered = False

    def _register_defaults_unlocked(self) -> None:
        """Helper to register standard domain agents without acquiring lock again."""
        if self._defaults_registered:
            return
        self._defaults_registered = True

        defaults: List[Tuple[str, str, str]] = [
            ("react", "optimization_core.agents.framework.architectures.react_agent", "ReActAgent"),
            ("code_interpreter", "optimization_core.agents.domains.code_interpreter", "CodeInterpreterAgent"),
            ("data_analysis", "optimization_core.agents.domains.data_analysis", "DataAnalysisAgent"),
            ("embodied_rl", "optimization_core.agents.domains.embodied_rl.rl_agent", "RLAgent"),
            ("math", "optimization_core.agents.domains.formal_verification.math_agent", "MathAgent"),
            ("marketing", "optimization_core.agents.domains.marketing_intelligence.marketing_agent", "MarketingAgent"),
            ("research", "optimization_core.agents.domains.system_intelligence.research_agent", "ResearchAgent"),
            ("system", "optimization_core.agents.domains.system_intelligence.system_agent", "SystemAgent"),
            ("blockchain", "optimization_core.agents.domains.blockchain.blockchain_agent", "BlockchainAgent"),
        ]

        import importlib
        for key, module_path, class_name in defaults:
            if key not in self._classes:
                try:
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name)
                    self._classes[key] = cls
                except Exception as exc:
                    logger.debug("Failed to auto-register default agent '%s': %s", key, exc)

    def register_defaults(self) -> None:
        """Explicitly register built-in domain agents."""
        with self._registry_lock:
            self._register_defaults_unlocked()

    def create(self, agent_type: str, name: str, role: str, **kwargs: Any) -> BaseAgent:
        """Instantiate, register, and return a new agent of type `agent_type`."""
        agent_cls = self.get_class(agent_type)
        if agent_cls is None:
            raise RegistryError(f"Agent type '{agent_type}' is not registered in AgentRegistry.")
        instance = agent_cls(name=name, role=role, **kwargs)
        self.register_instance(name, instance)
        return instance


agent_registry = AgentRegistry.get_instance()

__all__ = ["AgentRegistry", "agent_registry"]


