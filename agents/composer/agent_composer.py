"""
System 5.9 — Agent Composer.

Allows users to create custom agent combinations by selecting
tools, capabilities, and verification layers from a catalog.
Compositions are saved as reusable blueprints.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..arquitecturas_fundamentales.base_agent import BaseAgent
from ..models import AgentResponse, AgentConfig
from ..razonamiento_planificacion.tools import BaseTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Composable capability catalog
# ---------------------------------------------------------------------------

def _build_catalog() -> Dict[str, Dict[str, Any]]:
    """
    Build the full catalog of composable capabilities.

    Each entry has:
    - description: human-readable
    - tools: dict of tool_name -> tool_class
    - category: for grouping in the UI
    """
    catalog = {}

    # Math & Formal Verification
    try:
        from ..formal_verification.math_agent import MATH_TOOLS
        catalog["math_symbolic"] = {
            "description": "SymPy: Álgebra simbólica, cálculo, ecuaciones",
            "tools": {"sympy_verify": MATH_TOOLS["sympy_verify"]},
            "category": "Mathematics",
        }
        catalog["math_lean4"] = {
            "description": "Lean 4: Pruebas formales de teoremas",
            "tools": {"lean4_verify": MATH_TOOLS["lean4_verify"]},
            "category": "Formal Verification",
        }
        catalog["math_z3"] = {
            "description": "Z3 SMT: Resolución de restricciones lógicas",
            "tools": {"z3_verify": MATH_TOOLS["z3_verify"]},
            "category": "Formal Verification",
        }
        catalog["math_numerical"] = {
            "description": "NumPy/SciPy: Eigenvalores, SVD, raíces numéricas",
            "tools": {"numerical_verify": MATH_TOOLS["numerical_verify"]},
            "category": "Mathematics",
        }
        catalog["code_verify"] = {
            "description": "mypy + AST: Verificación de tipos y análisis estático",
            "tools": {"code_verify": MATH_TOOLS["code_verify"]},
            "category": "Code Quality",
        }
    except ImportError:
        logger.warning("Math tools not available for catalog")

    # Core Tools
    try:
        from ..razonamiento_planificacion.tools import (
            WebSearchTool, WebReaderTool, FileReadTool, FileWriteTool,
            PythonExecutionTool, SystemBashTool,
        )
        catalog["web_search"] = {
            "description": "Búsqueda web con DuckDuckGo + degradación automática",
            "tools": {"web_search": WebSearchTool},
            "category": "Research",
        }
        catalog["web_reader"] = {
            "description": "Lectura y extracción de contenido web",
            "tools": {"web_reader": WebReaderTool},
            "category": "Research",
        }
        catalog["file_ops"] = {
            "description": "Lectura y escritura de archivos locales",
            "tools": {"file_read": FileReadTool, "file_write": FileWriteTool},
            "category": "System",
        }
        catalog["python_exec"] = {
            "description": "Ejecución de código Python en sandbox",
            "tools": {"python_execute": PythonExecutionTool},
            "category": "Code Execution",
        }
        catalog["system_bash"] = {
            "description": "Ejecución de comandos del sistema",
            "tools": {"system_bash": SystemBashTool},
            "category": "System",
        }
    except ImportError:
        logger.warning("Core tools not available for catalog")

    # Research Tools
    try:
        from ..system_intelligence.system_tools import (
            ArXivSearchTool, GoogleScholarSearchTool, GitHubSearchTool,
        )
        catalog["arxiv_search"] = {
            "description": "Búsqueda de papers en ArXiv",
            "tools": {"arxiv_search": ArXivSearchTool},
            "category": "Research",
        }
        catalog["scholar_search"] = {
            "description": "Búsqueda en Google Scholar",
            "tools": {"google_scholar_search": GoogleScholarSearchTool},
            "category": "Research",
        }
        catalog["github_search"] = {
            "description": "Búsqueda de repositorios en GitHub",
            "tools": {"github_search": GitHubSearchTool},
            "category": "Research",
        }
    except ImportError:
        logger.warning("Research tools not available for catalog")

    return catalog


# ---------------------------------------------------------------------------
# Blueprint persistence
# ---------------------------------------------------------------------------

BLUEPRINTS_DIR = Path("truthgpt_collected/agent_blueprints")


def save_blueprint(name: str, capabilities: List[str], meta: dict) -> Path:
    """Save a custom agent blueprint to disk."""
    BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    bp = {
        "name": name,
        "capabilities": capabilities,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        **meta,
    }
    path = BLUEPRINTS_DIR / f"{name.lower().replace(' ', '_')}.json"
    path.write_text(json.dumps(bp, indent=2), encoding="utf-8")
    logger.info("Blueprint saved: %s", path)
    return path


def load_blueprints() -> List[dict]:
    """Load all saved blueprints."""
    if not BLUEPRINTS_DIR.exists():
        return []
    results = []
    for f in sorted(BLUEPRINTS_DIR.glob("*.json")):
        try:
            results.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
# Composed Agent (runtime)
# ---------------------------------------------------------------------------

class ComposedAgent(BaseAgent):
    """
    A dynamically-composed agent built from user-selected capabilities.

    Created by the Agent Composer from a blueprint or interactive selection.
    """

    def __init__(
        self,
        name: str = "CustomAgent",
        role: str = "Custom Composed Agent",
        capabilities: Optional[List[str]] = None,
        config: Optional[AgentConfig] = None,
        llm_engine: Optional[Any] = None,
    ) -> None:
        super().__init__(name=name, role=role)
        self.llm = llm_engine
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self._capability_keys: List[str] = capabilities or []

        # Build tools from capabilities
        catalog = _build_catalog()
        for cap_key in self._capability_keys:
            if cap_key in catalog:
                for tool_name, tool_cls in catalog[cap_key]["tools"].items():
                    self.tools[tool_name] = tool_cls()
                    logger.info("ComposedAgent '%s': loaded tool '%s'", name, tool_name)

    async def process(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        logger.info("ComposedAgent '%s' processing: %s", self.name, query[:80])

        # Try auto-routing to tools
        for tool in self.tools.values():
            # Check if the tool can handle this query
            q_lower = query.strip().lower()
            tool_name_lower = tool.name.lower()

            # Simple keyword matching for routing
            if tool_name_lower.replace("_", " ") in q_lower or tool_name_lower in q_lower:
                result = await tool.run(query)
                return AgentResponse(
                    content=result,
                    action_type="final_answer",
                    metadata={"agent": self.name, "tool_used": tool.name},
                )

        # LLM-assisted routing
        if self.llm:
            tools_desc = "\n".join(
                f"- {t.name}: {t.description}" for t in self.tools.values()
            )
            prompt = (
                f"Eres '{self.name}', un agente especializado con estas herramientas:\n"
                f"{tools_desc}\n\n"
                f"Solicitud del usuario: {query}\n\n"
                f"Razona paso a paso y responde."
            )
            try:
                response = await self.llm(prompt)
                return AgentResponse(
                    content=response,
                    action_type="final_answer",
                    metadata={"agent": self.name, "method": "llm"},
                )
            except Exception as e:
                logger.error("ComposedAgent LLM error: %s", e)

        # Fallback: describe capabilities
        caps = ", ".join(self._capability_keys) if self._capability_keys else "ninguna"
        tools_list = ", ".join(self.tools.keys()) if self.tools else "ninguna"
        return AgentResponse(
            content=(
                f"Soy '{self.name}' con capacidades: {caps}\n"
                f"Herramientas: {tools_list}\n\n"
                f"Reformula tu consulta para que pueda ayudarte."
            ),
            action_type="final_answer",
        )

    def get_capability_summary(self) -> str:
        """Return a human-readable summary of this agent's capabilities."""
        catalog = _build_catalog()
        lines = []
        for key in self._capability_keys:
            if key in catalog:
                lines.append(f"  • {catalog[key]['description']}")
        return "\n".join(lines) if lines else "  (sin capacidades)"
