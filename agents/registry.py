"""
Centralized Component Registry for TruthGPT — Pydantic-First.

Provides a singleton registry for discovering, registering, and
introspecting both tools and agents available to the ecosystem.
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from .razonamiento_planificacion.tools import (
    BaseTool,
)
from .arquitecturas_fundamentales.base_agent import BaseAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ToolInfo(BaseModel):
    """Structured introspection data for a registered tool."""
    name: str
    class_name: str
    module: str = ""
    has_run: bool = True


class AgentInfo(BaseModel):
    """Structured introspection data for a registered agent."""
    name: str
    role: str
    class_name: str
    module: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ComponentRegistry:
    """Dynamic singleton registry for TruthGPT components (tools and agents)."""

    _instance = None
    _tools: Dict[str, Type[BaseTool]] = {}
    _agents: Dict[str, Type[BaseAgent]] = {}
    
    # Lazy loading maps: name -> (module_path, class_name)
    _tool_map: Dict[str, tuple] = {}
    _agent_map: Dict[str, tuple] = {}

    def __new__(cls) -> "ComponentRegistry":
        if cls._instance is None:
            cls._instance = super(ComponentRegistry, cls).__new__(cls)
            cls._instance._init_builtins()
            cls._instance.discover_plugins()
        return cls._instance

    def _init_builtins(self) -> None:
        """Populate lazy-loading maps for core components."""
        # Core reasoning tools
        core_tools_mod = "agents.razonamiento_planificacion.tools"
        self._tool_map.update({
            "system_bash": (core_tools_mod, "SystemBashTool"),
            "web_search": (core_tools_mod, "WebSearchTool"),
            "web_reader": (core_tools_mod, "WebReaderTool"),
            "file_read": (core_tools_mod, "FileReadTool"),
            "file_write": (core_tools_mod, "FileWriteTool"),
            "python_execute": (core_tools_mod, "PythonExecutionTool"),
            "delegate_task": (core_tools_mod, "DelegateTaskTool"),
            "directory_list": (core_tools_mod, "DirectoryListTool"),
            "glob_search": (core_tools_mod, "GlobTool"),
            "notebook_edit": (core_tools_mod, "NotebookEditTool"),
        })

        # System intelligence tools
        sys_tools_mod = "agents.system_intelligence.system_tools"
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
            "research_agent": ("agents.system_intelligence.research_agent", "ResearchAgent"),
            "marketing_agent": ("agents.marketing_intelligence.marketing_agent", "MarketingAgent"),
            "rl_agent": ("agents.embodied_rl.rl_agent", "RLAgent"),
            "system_agent": ("agents.system_intelligence.system_agent", "SystemAgent"),
            "blockchain_agent": ("agents.blockchain.blockchain_agent", "BlockchainAgent"),
            "code_architect": ("agents.code_interpreter", "CodeInterpreterAgent"),
            "planning_agent": ("agents.multi_agentes.planning_agent", "PlanningAgent"),
            "forensic_agent": ("agents.system_intelligence.system_agent", "SystemAgent"),
            "data_analysis": ("agents.data_analysis", "DataAnalysisAgent"),
            "arxiv_discovery_scout": ("agents.system_intelligence.research_agent", "ResearchAgent"),
            "sota_integrator": ("agents.system_intelligence.research_agent", "ResearchAgent"),
            "security_analyst": ("agents.system_intelligence.system_agent", "SystemAgent"),
            "defi_expert": ("agents.blockchain.blockchain_agent", "BlockchainAgent"),
            "evolution_architect": ("agents.system_intelligence.evolution_architect", "EvolutionArchitect"),
        })
        
        # Math tools are special as they might fail to import
        try:
            # We still keep this part a bit dynamic but we could also lazy-load it
            self._agent_map["math_verifier"] = ("agents.formal_verification.math_agent", "MathVerificationAgent")
        except: pass

    # --- Tool Management ---

    def register_tool(self, name: str, tool_cls: Type[BaseTool]) -> None:
        """Manually register a tool."""
        self._tools[name] = tool_cls
        logger.info("Tool registered: %s -> %s", name, tool_cls.__name__)

    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        """Retrieve a tool, loading it lazily if necessary."""
        if name in self._tools:
            return self._tools[name]
        
        if name in self._tool_map:
            module_path, class_name = self._tool_map[name]
            try:
                module = importlib.import_module(module_path)
                if class_name == "plugin":
                    # Look for subclasses of BaseTool in the module
                    for attr_name, obj in inspect.getmembers(module):
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
        
        # Check math tools lazily too
        if name.startswith("math_") or name in ["solve", "prove", "simplify"]:
             try:
                 from agents.formal_verification.math_agent import MATH_TOOLS
                 if name in MATH_TOOLS:
                     self._tools[name] = MATH_TOOLS[name]
                     return MATH_TOOLS[name]
             except: pass

        return None

    def get_all_tools(self) -> Dict[str, Type[BaseTool]]:
        """Return all valid registered tools (forces loading of all built-ins)."""
        # For introspection, we might need to load everything
        for name in list(self._tool_map.keys()):
            self.get_tool(name)
        return {
            k: v for k, v in self._tools.items()
            if isinstance(k, str) and not k.startswith("__")
        }

    def list_tools(self) -> List[ToolInfo]:
        """Return structured Pydantic introspection of all registered tools."""
        return [
            ToolInfo(
                name=name,
                class_name=cls.__name__,
                module=cls.__module__ if hasattr(cls, "__module__") else "",
                has_run=hasattr(cls, "run") or hasattr(cls, "process"),
            )
            for name, cls in self.get_all_tools().items()
        ]

    # --- Agent Management ---

    def register_agent(self, name: str, agent_cls: Type[BaseAgent]) -> None:
        """Manually register an agent."""
        self._agents[name] = agent_cls
        logger.info("Agent registered: %s -> %s", name, agent_cls.__name__)

    def get_agent(self, name: str) -> Optional[Type[BaseAgent]]:
        """Retrieve an agent, loading it lazily if necessary."""
        if name in self._agents:
            return self._agents[name]
        
        if name in self._agent_map:
            module_path, class_name = self._agent_map[name]
            try:
                module = importlib.import_module(module_path)
                if class_name == "plugin":
                    for attr_name, obj in inspect.getmembers(module):
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
        for name in list(self._agent_map.keys()):
            self.get_agent(name)
        return dict(self._agents)

    def list_agents(self) -> List[AgentInfo]:
        """Return structured Pydantic introspection of all registered agents."""
        return [
            AgentInfo(
                name=name,
                role=getattr(cls, "role", "Unknown Role"),
                class_name=cls.__name__,
                module=cls.__module__,
            )
            for name, cls in self._agents.items()
        ]

    def register(self, name: str, cls: Type[Any]) -> None:
        """
        Generic registration method.

        Routes to register_tool or register_agent based on the class type.
        """
        if issubclass(cls, BaseTool):
            self.register_tool(name, cls)
        elif issubclass(cls, BaseAgent):
            self.register_agent(name, cls)
        else:
            logger.warning("ComponentRegistry: Unknown component type for %s (%s)", name, cls)
            # Fallback to tool if it's not an agent but we want to try anyway
            self._tools[name] = cls

    # --- Discovery ---

    def discover_plugins(self, plugins_dir: str = "plugins") -> None:
        """Dynamically discover tools and agents from a directory without importing them."""
        path = Path(plugins_dir)
        if not path.exists():
            return

        for file in path.glob("*.py"):
            if file.name == "__init__.py":
                continue

            module_name = f"{plugins_dir}.{file.stem}"
            # Store in lazy maps for later discovery
            # We don't know if it's a tool or agent yet, so we'll check on demand
            # or just register the module for later inspection
            self._tool_map[file.stem] = (module_name, "plugin") 
            self._agent_map[file.stem] = (module_name, "plugin")
            logger.debug("Plugin discovered (lazy): %s", file.stem)


# Global singleton
registry = ComponentRegistry()

# Backward-compatible aliases
ToolRegistry = ComponentRegistry
register = registry.register_tool
get_tool = registry.get_tool
get_all_tools = registry.get_all_tools
list_tools = registry.list_tools

# New Agent API
register_agent = registry.register_agent
get_agent = registry.get_agent
get_all_agents = registry.get_all_agents
list_agents = registry.list_agents

