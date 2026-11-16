"""
ADKOrchestratorAgent — Multi-agent coordinator using Google ADK.

Routes incoming tasks to the most appropriate specialized ADK sub-agent
(Research, Code, or General), supports parallel fan-out for hybrid tasks,
aggregates their outputs, and returns a unified response.

Architecture::

    ADKOrchestratorAgent
    ├── ADKResearchAgent   ← research / fact-check tasks
    ├── ADKCodeAgent       ← coding / engineering tasks
    └── (self/general)     ← fallback general-purpose

Usage::

    orchestrator = ADKOrchestratorAgent(api_key="...")
    result = await orchestrator.process(
        "Explain transformer attention and write a minimal PyTorch implementation."
    )
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from agents.framework.architectures.base_agent import (
    AgentLifecycleState,
    MemoryEntry,
)
from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_research_agent import ADKResearchAgent
from agents.domains.google_adk.adk_code_agent import ADKCodeAgent

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Task classifier
# ═══════════════════════════════════════════════════════════════════════════

_CODE_KEYWORDS: Set[str] = {
    "code", "implement", "write", "debug", "fix", "refactor", "function",
    "class", "script", "algorithm", "optimize", "review", "test", "unittest",
    "python", "javascript", "typescript", "rust", "go", "sql", "bash",
    "api", "endpoint", "deploy", "docker", "pipeline", "ci", "cd",
}

_RESEARCH_KEYWORDS: Set[str] = {
    "research", "explain", "what is", "how does", "analyze", "compare",
    "study", "investigate", "find", "search", "fact", "truth", "verify",
    "paper", "history", "why", "define", "summarize", "evaluate",
    "evidence", "source", "cite", "reference", "literature",
}

# Minimum score required to trigger a domain route
_CLASSIFICATION_THRESHOLD = 1


def classify_task(prompt: str) -> str:
    """Heuristically classify *prompt* as ``code``, ``research``, or ``general``.

    Returns one of: ``"code"``, ``"research"``, ``"general"``.
    """
    lower = prompt.lower()
    code_score = sum(1 for kw in _CODE_KEYWORDS if kw in lower)
    research_score = sum(1 for kw in _RESEARCH_KEYWORDS if kw in lower)

    if code_score > research_score and code_score >= _CLASSIFICATION_THRESHOLD:
        return "code"
    if research_score >= _CLASSIFICATION_THRESHOLD:
        return "research"
    return "general"


def classify_task_detailed(prompt: str) -> Dict[str, Any]:
    """Return classification result with scores and matched keywords for debugging."""
    lower = prompt.lower()
    code_hits = [kw for kw in _CODE_KEYWORDS if kw in lower]
    research_hits = [kw for kw in _RESEARCH_KEYWORDS if kw in lower]

    task_type = classify_task(prompt)
    return {
        "task_type": task_type,
        "code_score": len(code_hits),
        "research_score": len(research_hits),
        "code_keywords": code_hits,
        "research_keywords": research_hits,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Orchestrator agent
# ═══════════════════════════════════════════════════════════════════════════

class ADKOrchestratorAgent(ADKGeminiAgent):
    """
    Multi-agent orchestrator that delegates tasks to specialized ADK agents.

    Inherits full ``BaseAgent`` lifecycle management from ``ADKGeminiAgent``
    and overrides ``process()`` to add intelligent routing.

    Supports:
    - Single-route dispatch (code, research, general)
    - Parallel fan-out for hybrid prompts via ``process_parallel()``
    - Routing statistics via ``routing_stats``
    """

    def __init__(
        self,
        name: str = "adk-orchestrator",
        model: str = "gemini-2.5-pro",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            role="gemini-adk-orchestrator",
            instruction=(
                "You are a multi-agent orchestrator. You coordinate specialized "
                "agents to solve complex tasks that may require both research and "
                "coding capabilities. Synthesize their outputs into a coherent, "
                "well-structured final response."
            ),
            model=model,
            api_key=api_key,
        )
        self._research_agent = ADKResearchAgent(
            name=f"{name}-research", model=model, api_key=api_key,
        )
        self._code_agent = ADKCodeAgent(
            name=f"{name}-code", model=model, api_key=api_key,
        )
        self._routing_counter: Counter = Counter()

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _get_sub_agent(self, task_type: str) -> ADKGeminiAgent:
        """Return the sub-agent mapped to *task_type*."""
        if task_type == "code":
            return self._code_agent
        if task_type == "research":
            return self._research_agent
        return self  # general fallback uses the orchestrator's own ADK agent

    # ------------------------------------------------------------------
    # Override process() from ADKGeminiAgent
    # ------------------------------------------------------------------

    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Classify *query*, dispatch to the right sub-agent, and return the result.

        Falls through to ``ADKGeminiAgent.process()`` for general tasks.
        """
        classification = classify_task_detailed(query)
        task_type = classification["task_type"]
        self._routing_counter[task_type] += 1

        logger.info(
            "[%s] Routing task → %s (code=%d, research=%d)",
            self.name, task_type,
            classification["code_score"],
            classification["research_score"],
        )

        started = time.monotonic()
        agent = self._get_sub_agent(task_type)

        if agent is self:
            # General path — delegate to the parent's process()
            result = await super().process(query, context)
        else:
            result = await agent.process(query, context)

        elapsed = round(time.monotonic() - started, 3)

        # Record in the orchestrator's own memory
        self.add_to_memory("user", query)
        self.add_to_memory("assistant", self._extract_text(result), metadata={
            "routed_to": task_type,
            "classification": classification,
            "latency_s": elapsed,
        })

        return result

    # ------------------------------------------------------------------
    # Fan-out for hybrid prompts
    # ------------------------------------------------------------------

    async def process_parallel(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run *query* against both Code and Research agents in parallel.

        Returns a dict with ``code_result``, ``research_result``, and
        ``latency_s``.  Useful when the prompt clearly requires both
        perspectives (e.g. "explain X and implement it").
        """
        started = time.monotonic()

        code_task = asyncio.create_task(
            self._code_agent.process(query, context)
        )
        research_task = asyncio.create_task(
            self._research_agent.process(query, context)
        )

        code_result, research_result = await asyncio.gather(
            code_task, research_task, return_exceptions=True,
        )

        elapsed = round(time.monotonic() - started, 3)
        self._routing_counter["parallel"] += 1

        self.add_to_memory("user", query, metadata={"mode": "parallel"})

        return {
            "code_result": self._safe_result(code_result),
            "research_result": self._safe_result(research_result),
            "latency_s": elapsed,
        }

    # ------------------------------------------------------------------
    # Stats & reset
    # ------------------------------------------------------------------

    @property
    def routing_stats(self) -> Dict[str, int]:
        """Routing counts by task type."""
        return dict(self._routing_counter)

    def reset(self) -> None:
        """Reset the orchestrator and all sub-agents."""
        super().reset()
        self._research_agent.reset()
        self._code_agent.reset()
        self._routing_counter.clear()
        logger.info("[%s] Orchestrator + sub-agents reset.", self.name)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_result(result: Any) -> Any:
        """Wrap exceptions returned from ``asyncio.gather`` into error dicts."""
        if isinstance(result, BaseException):
            return {"content": f"Error: {result}", "metadata": {"status": "error"}}
        return result
