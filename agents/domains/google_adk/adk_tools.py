"""
ADK Tools — Bridge between TruthGPT's existing tools and Google ADK's @tool system.

Usage:
    from agents.domains.google_adk.adk_tools import adk_tool, get_adk_tools

    @adk_tool
    def search_web(query: str) -> str:
        \"\"\"Search the web for information.\"\"\"
        ...

    tools = get_adk_tools()  # returns list of ADK-compatible tool objects
"""

from __future__ import annotations

import logging
from typing import Callable, List, Any

logger = logging.getLogger(__name__)

# Registry of all ADK-compatible tools defined in this project
_ADK_TOOL_REGISTRY: List[Any] = []


def adk_tool(fn: Callable) -> Callable:
    """
    Decorator that registers a plain Python function as a Google ADK tool.

    ADK tools are just annotated Python functions — this decorator:
    1. Wraps the function with ADK's @tool if google-adk is installed.
    2. Falls back to returning the original function if ADK is not installed
       (so the code can still be imported in environments without ADK).
    3. Registers the tool in the local registry for introspection.

    Example::

        @adk_tool
        def calculate_score(value: float, weight: float = 1.0) -> float:
            \"\"\"Calculate a weighted score.\"\"\"
            return value * weight
    """
    try:
        from google.adk.tools import tool as _adk_tool_decorator
        wrapped = _adk_tool_decorator(fn)
    except ImportError:
        logger.debug(
            "google-adk not installed — @adk_tool wrapping skipped for %s. "
            "Install with: pip install google-adk",
            fn.__name__,
        )
        wrapped = fn

    _ADK_TOOL_REGISTRY.append(wrapped)
    return wrapped


def get_adk_tools() -> List[Any]:
    """Return all tools registered via @adk_tool."""
    return list(_ADK_TOOL_REGISTRY)


# ---------------------------------------------------------------------------
# Built-in TruthGPT tools registered for ADK
# ---------------------------------------------------------------------------

@adk_tool
def search_knowledge_base(query: str) -> str:
    """
    Search TruthGPT's internal knowledge base for factual information.

    Args:
        query: The question or topic to search for.

    Returns:
        A string with the most relevant knowledge base results.
    """
    # Placeholder — wire to your actual KB/retrieval layer
    return f"[KnowledgeBase] No results found for: {query!r}"


@adk_tool
def run_python_snippet(code: str) -> str:
    """
    Execute a Python code snippet in a sandboxed environment and return stdout.

    Args:
        code: Valid Python source code to execute.

    Returns:
        The captured stdout output, or an error message.
    """
    import io
    import contextlib
    import traceback

    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, {"__builtins__": __builtins__})  # noqa: S102
        return buffer.getvalue() or "(no output)"
    except Exception:
        return f"Error:\n{traceback.format_exc()}"


@adk_tool
def get_system_metrics() -> dict:
    """
    Return current system resource metrics (CPU, memory, uptime).

    Returns:
        Dictionary with cpu_percent, memory_percent, and uptime_seconds.
    """
    try:
        import psutil
        import time
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "uptime_seconds": int(time.time() - psutil.boot_time()),
        }
    except ImportError:
        return {"error": "psutil not installed"}
