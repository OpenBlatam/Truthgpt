"""
Centralized Component Registry for TruthGPT — Pydantic-First.

Provides a thread-safe singleton registry for discovering, registering, and
introspecting both tools and agents available to the ecosystem.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Set, Tuple

from pydantic import BaseModel, Field

try:
    from optimization_core.agents.framework.tools.tools import BaseTool
except ImportError:
    from agents.framework.tools.tools import BaseTool

try:
    from optimization_core.agents.framework.architectures.base_agent import BaseAgent
except ImportError:
    from agents.framework.architectures.base_agent import BaseAgent

try:
    from optimization_core.agents.framework.exceptions import RegistryError, PluginLoadError
except ImportError:
    from agents.framework.exceptions import RegistryError, PluginLoadError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Introspection Models
# ---------------------------------------------------------------------------

class ToolInfo(BaseModel):
    """Structured introspection data for a registered tool."""
    name: str
    class_name: str
    module: str = ""
    category: str = "general"
    description: str = ""
    has_run: bool = True


class AgentInfo(BaseModel):
    """Structured introspection data for a registered agent."""
    name: str
    role: str
    class_name: str
    module: str = ""
    category: str = "domain"
    description: str = ""


# ---------------------------------------------------------------------------
# Thread-Safe Singleton Registry
# ---------------------------------------------------------------------------

class ComponentRegistry:
    """Dynamic thread-safe singleton registry for TruthGPT components (tools and agents)."""

    _instance: Optional[ComponentRegistry] = None
    _lock: threading.RLock = threading.RLock()

    def __new__(cls) -> ComponentRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ComponentRegistry, cls).__new__(cls)
                cls._instance._init_registry_state()
                cls._instance._init_builtins()
                cls._instance.discover_plugins()
            return cls._instance

    def _init_registry_state(self) -> None:
        """Initialize registry storage and lookup maps."""
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._tool_map: Dict[str, Tuple[str, str]] = {}
        self._agent_map: Dict[str, Tuple[str, str]] = {}
        self._on_register_hooks: List[Callable[[str, Any], None]] = []

    def _init_builtins(self) -> None:
        """Populate lazy-loading maps for core built-in components."""
        # Core reasoning tools
        core_tools_mod = "optimization_core.agents.framework.tools.tools"
        self._tool_map.update({
            "system_bash": (core_tools_mod, "SystemBashTool"),
            "web_search": (core_tools_mod, "WebSearchTool"),
            "web_reader": (core_tools_mod, "WebReaderTool"),
            "deep_research": (core_tools_mod, "DeepResearchTool"),
            "file_read": (core_tools_mod, "FileReadTool"),
            "file_write": (core_tools_mod, "FileWriteTool"),
            "python_execute": (core_tools_mod, "PythonExecutionTool"),
            "delegate_task": (core_tools_mod, "DelegateTaskTool"),
            "directory_list": (core_tools_mod, "DirectoryListTool"),
            "glob_search": (core_tools_mod, "GlobTool"),
            "notebook_edit": (core_tools_mod, "NotebookEditTool"),
        })

        # System intelligence tools
        sys_tools_mod = "optimization_core.agents.domains.system_intelligence.system_tools"
        self._tool_map.update({
            "system_papers_list": (sys_tools_mod, "ListPapersTool"),
            "system_papers_info": (sys_tools_mod, "PaperInfoTool"),
            "system_health": (sys_tools_mod, "SystemHealthTool"),
            "system_run_optimization": (sys_tools_mod, "RunOptimizationTool"),
            "system_model_inference": (sys_tools_mod, "ModelInferenceTool"),
            "system_model_train": (sys_tools_mod, "ModelTrainTool"),
            "arxiv_search": (sys_tools_mod, "ArXivSearchTool"),
            "google_scholar_search": (sys_tools_mod, "GoogleScholarSearchTool"),
            "semantic_scholar_search": (sys_tools_mod, "SemanticScholarSearchTool"),
            "github_search": (sys_tools_mod, "GitHubSearchTool"),
            "paper_synthesis": (sys_tools_mod, "PaperSynthesisTool"),
            "sota_scraper": (sys_tools_mod, "SOTAPaperScraperTool"),
        })

        # Agent Blueprints
        self._agent_map.update({
            "research_agent": ("optimization_core.agents.domains.system_intelligence.research_agent", "ResearchAgent"),
            "marketing_agent": ("optimization_core.agents.domains.marketing_intelligence.marketing_agent", "MarketingAgent"),
            "rl_agent": ("optimization_core.agents.domains.embodied_rl.rl_agent", "RLAgent"),
            "system_agent": ("optimization_core.agents.domains.system_intelligence.system_agent", "SystemAgent"),
            "blockchain_agent": ("optimization_core.agents.domains.blockchain.blockchain_agent", "BlockchainAgent"),
            "code_architect": ("optimization_core.agents.domains.code_interpreter", "CodeInterpreterAgent"),
            "planning_agent": ("optimization_core.agents.orchestration.swarm.planning_agent", "PlanningAgent"),
            "forensic_agent": ("optimization_core.agents.domains.system_intelligence.system_agent", "SystemAgent"),
            "data_analysis": ("optimization_core.agents.domains.data_analysis", "DataAnalysisAgent"),
            "arxiv_discovery_scout": ("optimization_core.agents.domains.system_intelligence.research_agent", "ResearchAgent"),
            "sota_integrator": ("optimization_core.agents.domains.system_intelligence.research_agent", "ResearchAgent"),
            "security_analyst": ("optimization_core.agents.domains.system_intelligence.system_agent", "SystemAgent"),
            "defi_expert": ("optimization_core.agents.domains.blockchain.blockchain_agent", "BlockchainAgent"),
            "evolution_architect": ("optimization_core.agents.domains.system_intelligence.evolution_architect", "EvolutionArchitect"),
        })
        
        # Formal verification math agent
        self._agent_map["math_verifier"] = (
            "optimization_core.agents.domains.formal_verification.math_agent",
            "MathVerificationAgent"
        )

    # --- Tool Management ---

    def register_tool(self, name: str, tool_cls: Type[BaseTool]) -> None:
        """Manually register a tool class."""
        with self._lock:
            self._tools[name] = tool_cls
            logger.info("Tool registered: %s -> %s", name, tool_cls.__name__)
            self._trigger_on_register_hooks(name, tool_cls)

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool by name."""
        with self._lock:
            removed = bool(self._tools.pop(name, None) or self._tool_map.pop(name, None))
            if removed:
                logger.info("Tool unregistered: %s", name)
            return removed

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered or lazily discoverable."""
        with self._lock:
            return name in self._tools or name in self._tool_map

    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        """Retrieve a tool class, loading it lazily if necessary."""
        with self._lock:
            if name in self._tools:
                return self._tools[name]
            
            if name in self._tool_map:
                module_path, class_name = self._tool_map[name]
                try:
                    module = importlib.import_module(module_path)
                    if class_name == "plugin":
                        for _, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                                tool_name = getattr(obj, "name", obj.__name__.lower())
                                self._tools[tool_name] = obj
                                if tool_name == name or obj.__name__ == name:
                                    return obj
                        return None
                    
                    tool_cls = getattr(module, class_name)
                    self._tools[name] = tool_cls
                    return tool_cls
                except Exception as e:
                    logger.error("Registry: Failed to lazy-load tool %s: %s", name, e)
            
            # Check math tools lazily
            if name.startswith("math_") or name in ["solve", "prove", "simplify"]:
                try:
                    from optimization_core.agents.domains.formal_verification.math_agent import MATH_TOOLS
                    if name in MATH_TOOLS:
                        self._tools[name] = MATH_TOOLS[name]
                        return MATH_TOOLS[name]
                except Exception:
                    pass

            return None

    def get_all_tools(self) -> Dict[str, Type[BaseTool]]:
        """Return all valid registered tools (forces loading of built-ins)."""
        with self._lock:
            for name in list(self._tool_map.keys()):
                self.get_tool(name)
            return {
                k: v for k, v in self._tools.items()
                if isinstance(k, str) and not k.startswith("__")
            }

    def list_tools(self, category: Optional[str] = None) -> List[ToolInfo]:
        """Return structured Pydantic introspection of all registered tools, optionally filtered by category."""
        tools = self.get_all_tools()
        infos: List[ToolInfo] = []
        for name, cls in tools.items():
            desc_attr = getattr(cls, "description", None)
            desc_str = desc_attr if isinstance(desc_attr, str) else (cls.__doc__ or "")
            tool_cat = getattr(cls, "category", "system" if "system" in name else "general")
            if category and tool_cat.lower() != category.lower():
                continue
            infos.append(
                ToolInfo(
                    name=name,
                    class_name=cls.__name__,
                    module=getattr(cls, "__module__", ""),
                    category=tool_cat,
                    description=desc_str.strip().split("\n")[0] if desc_str else "",
                    has_run=hasattr(cls, "run") or hasattr(cls, "process"),
                )
            )
        return infos

    # --- Agent Management ---

    def register_agent(self, name: str, agent_cls: Type[BaseAgent]) -> None:
        """Manually register an agent class."""
        with self._lock:
            self._agents[name] = agent_cls
            logger.info("Agent registered: %s -> %s", name, agent_cls.__name__)
            self._trigger_on_register_hooks(name, agent_cls)

    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent by name."""
        with self._lock:
            removed = bool(self._agents.pop(name, None) or self._agent_map.pop(name, None))
            if removed:
                logger.info("Agent unregistered: %s", name)
            return removed

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered or lazily discoverable."""
        with self._lock:
            return name in self._agents or name in self._agent_map

    def get_agent(self, name: str) -> Optional[Type[BaseAgent]]:
        """Retrieve an agent class, loading it lazily if necessary."""
        with self._lock:
            if name in self._agents:
                return self._agents[name]
            
            if name in self._agent_map:
                module_path, class_name = self._agent_map[name]
                try:
                    module = importlib.import_module(module_path)
                    if class_name == "plugin":
                        for _, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                                agent_name = getattr(obj, "name", obj.__name__)
                                self._agents[agent_name] = obj
                                if agent_name == name or obj.__name__ == name:
                                    return obj
                        return None

                    agent_cls = getattr(module, class_name)
                    self._agents[name] = agent_cls
                    return agent_cls
                except Exception as e:
                    logger.error("Registry: Failed to lazy-load agent %s: %s", name, e)
                    
            return None

    def get_all_agents(self) -> Dict[str, Type[BaseAgent]]:
        """Forces loading of all known agents for introspection."""
        with self._lock:
            for name in list(self._agent_map.keys()):
                self.get_agent(name)
            return dict(self._agents)

    def list_agents(self, category: Optional[str] = None) -> List[AgentInfo]:
        """Return structured Pydantic introspection of all registered agents, optionally filtered by category."""
        agents = self.get_all_agents()
        infos: List[AgentInfo] = []
        for name, cls in agents.items():
            doc = cls.__doc__ or ""
            agent_cat = getattr(cls, "category", "domain")
            if category and agent_cat.lower() != category.lower():
                continue
            infos.append(
                AgentInfo(
                    name=name,
                    role=getattr(cls, "role", "Domain Agent"),
                    class_name=cls.__name__,
                    module=getattr(cls, "__module__", ""),
                    category=agent_cat,
                    description=doc.strip().split("\n")[0] if doc else "",
                )
            )
        return infos

    def register(self, name: str, cls: Type[Any]) -> None:
        """Generic registration routing method."""
        if issubclass(cls, BaseTool):
            self.register_tool(name, cls)
        elif issubclass(cls, BaseAgent):
            self.register_agent(name, cls)
        else:
            logger.warning("ComponentRegistry: Unknown component type for %s (%s)", name, cls)
            self._tools[name] = cls

    def clear(self) -> None:
        """Clear dynamic memory registrations, maintaining built-in lookup maps."""
        with self._lock:
            self._tools.clear()
            self._agents.clear()
            self._on_register_hooks.clear()
            self._init_builtins()

    # --- Discovery & Lifecycle ---

    def discover_plugins(self, plugins_dir: str = "plugins") -> None:
        """Dynamically discover tools and agents from a directory without importing them."""
        path = Path(plugins_dir)
        if not path.exists():
            return

        with self._lock:
            for file in path.glob("*.py"):
                if file.name == "__init__.py":
                    continue

                module_name = f"{plugins_dir}.{file.stem}"
                self._tool_map[file.stem] = (module_name, "plugin") 
                self._agent_map[file.stem] = (module_name, "plugin")
                logger.debug("Plugin discovered (lazy): %s", file.stem)

    def add_on_register_hook(self, hook: Callable[[str, Any], None]) -> None:
        """Add a callback hook triggered when any new component is registered."""
        with self._lock:
            self._on_register_hooks.append(hook)

    def _trigger_on_register_hooks(self, name: str, component: Any) -> None:
        """Trigger registered hooks safely."""
        for hook in self._on_register_hooks:
            try:
                hook(name, component)
            except Exception as e:
                logger.warning("Error in registry on_register hook for %s: %s", name, e)


# Global singleton instance
registry = ComponentRegistry()

# Backward-compatible function aliases
ToolRegistry = ComponentRegistry
register = registry.register_tool
get_tool = registry.get_tool
get_all_tools = registry.get_all_tools
list_tools = registry.list_tools

register_agent = registry.register_agent
get_agent = registry.get_agent
get_all_agents = registry.get_all_agents
list_agents = registry.list_agents

