"""
ADKCodeAgent — Code generation, review, and debugging agent via Google ADK.

Specializes in software engineering tasks: generating code, explaining
algorithms, reviewing for bugs, writing tests, and optimizing performance.

Usage::

    agent = ADKCodeAgent()
    result = await agent.arun(
        "Write a Python async queue implementation with priority support."
    )
"""

from __future__ import annotations

import logging
from typing import Optional

from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_tools import adk_tool

logger = logging.getLogger(__name__)

_CODE_INSTRUCTION = """
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
- For reviews, use a structured format: ISSUES / SUGGESTIONS / SUMMARY.
""".strip()


@adk_tool
def analyze_code_complexity(code: str) -> dict:
    """
    Estimate the cyclomatic complexity and lines of code for a Python snippet.

    Args:
        code: Python source code to analyze.

    Returns:
        Dict with 'lines_of_code', 'blank_lines', 'comment_lines',
        and 'estimated_complexity' (LOW/MEDIUM/HIGH).
    """
    lines = code.splitlines()
    loc = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    branches = sum(
        1 for l in lines
        if any(kw in l for kw in ("if ", "elif ", "for ", "while ", "except ", "case "))
    )
    complexity = "LOW" if branches < 5 else ("MEDIUM" if branches < 15 else "HIGH")
    return {
        "lines_of_code": loc,
        "blank_lines": blank,
        "comment_lines": comments,
        "branch_count": branches,
        "estimated_complexity": complexity,
    }


@adk_tool
def detect_security_patterns(code: str) -> list:
    """
    Scan Python code for common security anti-patterns.

    Args:
        code: Python source code to scan.

    Returns:
        List of detected security concerns with line numbers and descriptions.
    """
    patterns = {
        "eval(": "Dangerous use of eval() — potential code injection",
        "exec(": "Dangerous use of exec() — potential code injection",
        "pickle.load": "Insecure deserialization via pickle",
        "subprocess.call(shell=True": "Shell injection risk in subprocess",
        "os.system(": "Shell injection risk via os.system()",
        "hashlib.md5(": "Weak hashing algorithm MD5 detected",
        "hashlib.sha1(": "Weak hashing algorithm SHA-1 detected",
        "password": "Potential hardcoded credential or plain-text password",
        "secret": "Potential hardcoded secret",
    }
    findings = []
    for i, line in enumerate(code.splitlines(), start=1):
        for pattern, description in patterns.items():
            if pattern.lower() in line.lower():
                findings.append({
                    "line": i,
                    "pattern": pattern,
                    "description": description,
                    "severity": "HIGH" if "injection" in description else "MEDIUM",
                })
    return findings


class ADKCodeAgent(ADKGeminiAgent):
    """
    Software engineering agent built on ADKGeminiAgent.

    Adds code-specific tools (complexity analysis, security scanning)
    and an engineering-optimized system prompt.
    """

    def __init__(
        self,
        name: str = "adk-code-agent",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            instruction=_CODE_INSTRUCTION,
            model="gemini-2.5-pro",
            api_key=api_key,
        )
        self.role = "gemini-adk-code"
