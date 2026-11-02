"""
ADK Tools — Typed registry bridging TruthGPT tools to Google ADK's @tool system.

Core API:
    @adk_tool            — register any Python function as an ADK tool
    get_adk_tools()      — return all registered tool callables
    get_tools_by_cat()   — filter tools by category tag
    list_tool_manifest() — structured manifest for introspection / UI

Categories:
    knowledge   — KB/RAG retrieval
    execution   — sandboxed code execution
    system      — host metrics and diagnostics
    math        — numeric utilities
    text        — string/NLP helpers

Usage::

    from agents.domains.google_adk.adk_tools import adk_tool, get_adk_tools

    @adk_tool(category="custom")
    def my_tool(x: int) -> int:
        \"\"\"Double a number.\"\"\"
        return x * 2

    all_tools = get_adk_tools()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry internals
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ToolEntry:
    """Metadata wrapper around a registered ADK tool."""

    name: str
    category: str
    description: str
    callable: Any  # ADK-wrapped callable (or raw fallback)


_ADK_TOOL_REGISTRY: Dict[str, ToolEntry] = {}


def _try_wrap_adk(fn: Callable) -> Callable:
    """Attempt to wrap *fn* with google.adk.tools.tool; return raw fn on ImportError."""
    try:
        from google.adk.tools import tool as _adk_tool_decorator
        return _adk_tool_decorator(fn)
    except ImportError:
        logger.debug(
            "google-adk not installed — ADK wrapping skipped for '%s'. "
            "Install with: pip install google-adk>=1.0.0",
            fn.__name__,
        )
        return fn


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------

def adk_tool(
    fn: Optional[Callable] = None,
    *,
    category: str = "general",
) -> Union[Callable, Callable[[Callable], Callable]]:
    """
    Register a Python function as a Google ADK tool.

    Can be used with or without arguments::

        @adk_tool
        def foo(x: int) -> int: ...

        @adk_tool(category="math")
        def bar(x: float) -> float: ...

    Args:
        fn:       The function (when used without parentheses).
        category: Logical grouping for the tool (default ``"general"``).
    """

    def _register(func: Callable) -> Callable:
        if func.__name__ in _ADK_TOOL_REGISTRY:
            logger.warning(
                "ADK tool '%s' already registered — skipping duplicate.",
                func.__name__,
            )
            return _ADK_TOOL_REGISTRY[func.__name__].callable

        wrapped = _try_wrap_adk(func)
        entry = ToolEntry(
            name=func.__name__,
            category=category,
            description=(func.__doc__ or "").strip().split("\n")[0],
            callable=wrapped,
        )
        _ADK_TOOL_REGISTRY[func.__name__] = entry
        return wrapped

    # Support bare @adk_tool (no parens)
    if fn is not None:
        return _register(fn)
    return _register


# ---------------------------------------------------------------------------
# Public query helpers
# ---------------------------------------------------------------------------

def get_adk_tools() -> List[Any]:
    """Return all registered tool callables (ADK-wrapped or raw)."""
    return [entry.callable for entry in _ADK_TOOL_REGISTRY.values()]


def get_tools_by_category(category: str) -> List[Any]:
    """Return tool callables filtered by *category*."""
    return [
        entry.callable
        for entry in _ADK_TOOL_REGISTRY.values()
        if entry.category == category
    ]


def list_tool_manifest() -> List[Dict[str, str]]:
    """Return a structured manifest of every registered tool (name, category, description)."""
    return [
        {"name": e.name, "category": e.category, "description": e.description}
        for e in _ADK_TOOL_REGISTRY.values()
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Built-in TruthGPT tools
# ═══════════════════════════════════════════════════════════════════════════

# ── Knowledge ──────────────────────────────────────────────────────────────

@adk_tool(category="knowledge")
def search_knowledge_base(query: str) -> str:
    """Search TruthGPT's internal knowledge base for factual information.

    Args:
        query: The question or topic to search for.

    Returns:
        The most relevant knowledge-base results as a formatted string.
    """
    # Wire to your RAG / vector-store retrieval layer
    return f"[KnowledgeBase] No results found for: {query!r}"


# ── Execution ─────────────────────────────────────────────────────────────

_SANDBOX_BUILTINS = {
    k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
    for k in (
        "abs", "all", "any", "bool", "dict", "enumerate", "filter",
        "float", "format", "frozenset", "getattr", "hasattr", "hash",
        "int", "isinstance", "issubclass", "iter", "len", "list", "map",
        "max", "min", "next", "object", "pow", "print", "property",
        "range", "repr", "reversed", "round", "set", "slice", "sorted",
        "str", "sum", "tuple", "type", "zip",
    )
    if (isinstance(__builtins__, dict) and k in __builtins__)
    or (not isinstance(__builtins__, dict) and hasattr(__builtins__, k))
}


@adk_tool(category="execution")
def run_python_snippet(code: str) -> str:
    """Execute a Python code snippet in a restricted sandbox and return stdout.

    Only safe built-in functions are available (no file I/O, no imports by
    default, no ``eval``/``exec``).  Use for quick computations and demos.

    Args:
        code: Valid Python source code to execute.

    Returns:
        Captured stdout output, or a formatted error traceback.
    """
    import io
    import contextlib
    import traceback

    buf = io.StringIO()
    sandbox: Dict[str, Any] = {"__builtins__": _SANDBOX_BUILTINS}
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<adk_sandbox>", "exec"), sandbox)  # noqa: S102
        output = buf.getvalue()
        return output if output else "(no output)"
    except Exception:
        return f"Error:\n{traceback.format_exc()}"


# ── System ────────────────────────────────────────────────────────────────

@adk_tool(category="system")
def get_system_metrics() -> dict:
    """Return host resource metrics: CPU, memory, disk, and uptime.

    Returns:
        Dictionary with cpu_percent, memory_percent, disk_percent,
        uptime_seconds, and python_version.
    """
    import platform

    base: Dict[str, Any] = {"python_version": platform.python_version()}
    try:
        import psutil

        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        base.update({
            "cpu_percent": psutil.cpu_percent(interval=0.3),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total_gb": round(vm.total / (1024 ** 3), 2),
            "memory_percent": vm.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "uptime_seconds": int(time.time() - psutil.boot_time()),
        })
    except ImportError:
        base["error"] = "psutil not installed — install with: pip install psutil"
    return base


@adk_tool(category="system")
def get_gpu_info() -> list:
    """Return GPU name, memory, and utilization for each detected device.

    Returns:
        List of dicts, one per GPU, with id, name, memory_total_mb,
        memory_used_mb, and utilization_percent.
    """
    try:
        import subprocess
        import json

        raw = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        )
        gpus = []
        for line in raw.strip().splitlines():
            idx, name, mem_total, mem_used, util = [p.strip() for p in line.split(",")]
            gpus.append({
                "id": int(idx),
                "name": name,
                "memory_total_mb": int(mem_total),
                "memory_used_mb": int(mem_used),
                "utilization_percent": int(util),
            })
        return gpus
    except FileNotFoundError:
        return [{"error": "nvidia-smi not found — no NVIDIA GPU detected"}]
    except Exception as exc:  # noqa: BLE001
        return [{"error": str(exc)}]


# ── Math ──────────────────────────────────────────────────────────────────

@adk_tool(category="math")
def evaluate_expression(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.

    Uses Python's ``ast.literal_eval`` with an augmented parser for basic
    arithmetic (+, -, *, /, **, %).  No arbitrary code execution.

    Args:
        expression: A mathematical expression, e.g. ``"3 * (4 + 5) ** 2"``.

    Returns:
        The result as a string, or an error message.
    """
    import ast
    import operator

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval_node(node.operand))
        raise ValueError(f"Unsupported expression node: {ast.dump(node)}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree)
        return str(result)
    except Exception as exc:  # noqa: BLE001
        return f"Error evaluating '{expression}': {exc}"


# ── Text ──────────────────────────────────────────────────────────────────

@adk_tool(category="text")
def summarize_text(text: str, max_sentences: int = 3) -> str:
    """Extract the first N sentences from text as a naive summary.

    Args:
        text:          The input text to summarize.
        max_sentences: Maximum number of sentences to return (default 3).

    Returns:
        A string containing up to *max_sentences* sentences.
    """
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    selected = sentences[: max(1, max_sentences)]
    return " ".join(selected)


@adk_tool(category="text")
def count_tokens_estimate(text: str) -> dict:
    """Estimate token count for a piece of text using a word-based heuristic.

    Rule of thumb: ~1.3 tokens per whitespace-delimited word for English.

    Args:
        text: The input text.

    Returns:
        Dict with word_count, estimated_tokens, and char_count.
    """
    words = text.split()
    return {
        "word_count": len(words),
        "estimated_tokens": int(len(words) * 1.3),
        "char_count": len(text),
    }
