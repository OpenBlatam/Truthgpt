"""
Advanced Web Search Plugin for TruthGPT.
Demonstrates dynamic tool registration and auto-discovery.
"""

import asyncio
from typing import Any, Optional
from agents.razonamiento_planificacion.tools import BaseTool, ToolResult

class AdvancedWebSearchPlugin(BaseTool):
    """
    Plugin tool that performs deep web searches.
    Automatically discovered by the OpenClaw Plugin System.
    """
    
    name: str = "advanced_search"
    description: str = (
        "Performs a deep search on the internet for specific information. "
        "Input should be a search query string. Returns relevant snippets."
    )
    
    async def run(self, tool_input: str) -> ToolResult:
        """
        Runs internet search using search_internet.
        """
        print(f"DEBUG: AdvancedWebSearchPlugin running query: {tool_input}")
        try:
            try:
                from utils.internet_search import search_internet
            except ImportError:
                try:
                    from optimization_core.utils.internet_search import search_internet
                except ImportError:
                    import sys
                    from pathlib import Path
                    sys.path.append(str(Path(__file__).resolve().parent.parent))
                    from utils.internet_search import search_internet

            results = await search_internet(tool_input)
            if results:
                formatted_lines = []
                for i, r in enumerate(results, 1):
                    formatted_lines.append(
                        f"{i}. **{r.get('title', '—')}**\n"
                        f"   {r.get('snippet', '')}\n"
                        f"   Link: {r.get('link', 'N/A')}"
                    )
                output_str = f"Resultados para '{tool_input}':\n\n" + "\n\n".join(formatted_lines)
            else:
                output_str = f"No se encontraron resultados en internet para: '{tool_input}'."
        except Exception as e:
            output_str = f"Error al buscar en internet para '{tool_input}': {str(e)}"
            results = []

        return ToolResult(
            output=output_str,
            metadata={
                "source": "advanced_search_plugin",
                "query": tool_input,
                "results": results
            }
        )

# Factory function for dynamic loading
def get_tool() -> BaseTool:
    return AdvancedWebSearchPlugin()

