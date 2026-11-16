"""
ADKCodeAgent — Code generation, review, and debugging agent via Google ADK.

Specializes in software engineering tasks: generating code, explaining
algorithms, reviewing for bugs, writing tests, and optimising performance.

Usage::

    agent = ADKCodeAgent()
    result = await agent.process(
        "Write a Python async queue implementation with priority support."
    )
"""

from __future__ import annotations

import ast
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_tools import adk_tool

logger = logging.getLogger(__name__)

_CODE_INSTRUCTION = """\
You are an expert software engineering agent integrated into the TruthGPT platform.
You specialize in writing high-quality, production-ready code.

Engineering Standards:
- Write clean, readable, well-documented code with type hints.
- Follow PEP 8 for Python; use idiomatic patterns for other languages.
- Always include docstrings and inline comments for complex logic.
- When reviewing code, identify: bugs, security issues, performance issues,
  style violations, and missing edge cases.
- When writing tests, cover: happy paths, edge cases, and error conditions.
- Prefer composition over inheritance. Prefer explicit over implicit.

Output Format:
- Wrap all code in fenced code blocks with the correct language tag.
- After each code block, provide a brief explanation of key decisions.
- For reviews, use a structured format: ISSUES / SUGGESTIONS / SUMMARY.\
"""

# ═══════════════════════════════════════════════════════════════════════════
# Code-domain tools
# ═══════════════════════════════════════════════════════════════════════════

_BRANCH_KEYWORDS = frozenset({
    "if", "elif", "else", "for", "while", "except",
    "case", "with", "assert", "raise",
})


@adk_tool(category="code")
def analyze_code_complexity(code: str) -> dict:
    """Estimate cyclomatic complexity and structural metrics for Python code.

    Counts branch-introducing keywords and tries AST-based function / class
    extraction when possible.

    Args:
        code: Python source code to analyse.

    Returns:
        Dict with lines_of_code, blank_lines, comment_lines, branch_count,
        functions, classes, and estimated_complexity (LOW / MEDIUM / HIGH).
    """
    lines = code.splitlines()
    loc = len(lines)
    blank = sum(1 for ln in lines if not ln.strip())
    comments = sum(1 for ln in lines if ln.strip().startswith("#"))
    branches = sum(
        1 for ln in lines
        for kw in _BRANCH_KEYWORDS
        if re.search(rf"\b{kw}\b", ln)
    )

    # Try AST for richer info
    functions: List[str] = []
    classes: List[str] = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
    except SyntaxError:
        pass  # non-Python or invalid code

    if branches < 5:
        complexity = "LOW"
    elif branches < 15:
        complexity = "MEDIUM"
    else:
        complexity = "HIGH"

    return {
        "lines_of_code": loc,
        "blank_lines": blank,
        "comment_lines": comments,
        "branch_count": branches,
        "functions": functions,
        "classes": classes,
        "estimated_complexity": complexity,
    }


# Severity classification
_CRITICAL_PATTERNS: List[Tuple[str, str]] = [
    ("eval(", "Dangerous eval() — potential code injection"),
    ("exec(", "Dangerous exec() — potential code injection"),
    ("pickle.load", "Insecure deserialization via pickle"),
    ("yaml.load(", "Insecure YAML load (use yaml.safe_load)"),
    ("subprocess.call(", "Potential shell injection in subprocess.call"),
    ("subprocess.Popen(", "Potential shell injection in subprocess.Popen"),
    ("os.system(", "Shell injection risk via os.system()"),
]

_HIGH_PATTERNS: List[Tuple[str, str]] = [
    ("shell=True", "Shell=True enables shell injection"),
    ("__import__", "Dynamic import — potential injection vector"),
    ("marshal.load", "Insecure deserialization via marshal"),
]

_MEDIUM_PATTERNS: List[Tuple[str, str]] = [
    ("hashlib.md5(", "Weak hashing algorithm MD5"),
    ("hashlib.sha1(", "Weak hashing algorithm SHA-1"),
    ("password", "Potential hardcoded credential"),
    ("secret", "Potential hardcoded secret"),
    ("api_key", "Potential hardcoded API key"),
    ("token", "Potential hardcoded token"),
]


@adk_tool(category="code")
def detect_security_patterns(code: str) -> dict:
    """Scan Python code for common security anti-patterns.

    Classifies findings as CRITICAL, HIGH, or MEDIUM severity.

    Args:
        code: Python source code to scan.

    Returns:
        Dict with ``findings`` list and ``risk_summary`` counts.
    """
    findings: List[Dict[str, Any]] = []

    for severity, patterns in [
        ("CRITICAL", _CRITICAL_PATTERNS),
        ("HIGH", _HIGH_PATTERNS),
        ("MEDIUM", _MEDIUM_PATTERNS),
    ]:
        for pattern, description in patterns:
            for i, line in enumerate(code.splitlines(), start=1):
                if pattern.lower() in line.lower():
                    findings.append({
                        "line": i,
                        "pattern": pattern,
                        "description": description,
                        "severity": severity,
                    })

    risk_summary = {
        "CRITICAL": sum(1 for f in findings if f["severity"] == "CRITICAL"),
        "HIGH": sum(1 for f in findings if f["severity"] == "HIGH"),
        "MEDIUM": sum(1 for f in findings if f["severity"] == "MEDIUM"),
        "total": len(findings),
    }

    return {"findings": findings, "risk_summary": risk_summary}


@adk_tool(category="code")
def extract_imports(code: str) -> dict:
    """Extract all import statements from Python source code via AST.

    Args:
        code: Python source code.

    Returns:
        Dict with ``stdlib`` and ``third_party`` import lists (heuristic split).
    """
    import sys

    stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()

    imports: List[str] = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except SyntaxError:
        # Fallback to regex for broken code
        for match in re.finditer(
            r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", code, re.MULTILINE
        ):
            imports.append(match.group(1) or match.group(2))

    unique = sorted(set(imports))
    stdlib = [m for m in unique if m.split(".")[0] in stdlib_modules]
    third_party = [m for m in unique if m.split(".")[0] not in stdlib_modules]

    return {"stdlib": stdlib, "third_party": third_party}


# ═══════════════════════════════════════════════════════════════════════════
# Agent class
# ═══════════════════════════════════════════════════════════════════════════

class ADKCodeAgent(ADKGeminiAgent):
    """
    Software engineering agent built on ``ADKGeminiAgent``.

    Inherits the full ``BaseAgent`` lifecycle and ADK session management.
    Adds code-specific tools (complexity analysis, security scanning,
    import extraction) and an engineering-optimised system prompt.
    """

    def __init__(
        self,
        name: str = "adk-code-agent",
        model: str = "gemini-2.5-pro",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            role="gemini-adk-code",
            instruction=_CODE_INSTRUCTION,
            model=model,
            api_key=api_key,
        )
