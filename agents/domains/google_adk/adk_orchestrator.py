"""
ADKOrchestratorAgent — Multi-agent coordinator using Google ADK.

Routes incoming tasks to the most appropriate specialized ADK sub-agent
(Research, Code, or General), aggregates their outputs, and returns
a unified response.

Architecture::

    ADKOrchestratorAgent
    ├── ADKResearchAgent   ← for research/fact-check tasks
    ├── ADKCodeAgent       ← for coding/engineering tasks
    └── ADKGeminiAgent     ← fallback general-purpose agent

Usage::

    orchestrator = ADKOrchestratorAgent(api_key="...")
    result = await orchestrator.arun(
        "Explain transformer attention and write a minimal PyTorch implementation."
    )
"""

from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict, Optional

from agents.framework.architectures.base_agent import (
    AgentLifecycleState,
    AgentStatus,
    MemoryEntry,
)
from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_research_agent import ADKResearchAgent
from agents.domains.google_adk.adk_code_agent import ADKCodeAgent

logger = logging.getLogger(__name__)

# Task classification keywords
_CODE_KEYWORDS = {
    "code", "implement", "write", "debug", "fix", "refactor", "function",
    "class", "script", "algorithm", "optimize", "review", "test", "unittest",
    "python", "javascript", "typescript", "rust", "go", "sql", "bash",
}

_RESEARCH_KEYWORDS = {
    "research", "explain", "what is", "how does", "analyze", "compare",
    "study", "investigate", "find", "search", "fact", "truth", "verify",
    "paper", "study", "history", "why", "define", "summarize",
}


def _classify_task(prompt: str) -> str:
    """
    Heuristically classify a prompt as 'code', 'research', or 'general'.

    Returns one of: 'code', 'research', 'general'.
    """
    lower = prompt.lower()
    code_score = sum(1 for kw in _CODE_KEYWORDS if kw in lower)
    research_score = sum(1 for kw in _RESEARCH_KEYWORDS if kw in lower)

    if code_score > research_score and code_score > 0:
        return "code"
    elif research_score > 0:
        return "research"
    return "general"


class ADKOrchestratorAgent(ADKGeminiAgent):
    """
    Multi-agent orchestrator that delegates tasks to specialized ADK agents.

    Inherits lifecycle management from ADKGeminiAgent but overrides
    ``arun()`` to route tasks intelligently.
    """

    def __init__(
        self,
        name: str = "adk-orchestrator",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            instruction=(
                "You are a multi-agent orchestrator. You coordinate specialized "
                "agents to solve complex tasks that may require both research and "
                "coding capabilities. Synthesize their outputs into a coherent, "
                "well-structured final response."
            ),
            model="gemini-2.5-pro",
            api_key=api_key,
        )
        self.role = "gemini-adk-orchestrator"
        self._research_agent = ADKResearchAgent(
            name=f"{name}-research", api_key=api_key
        )
        self._code_agent = ADKCodeAgent(
            name=f"{name}-code", api_key=api_key
        )

    # ------------------------------------------------------------------
    # Routing logic
    # ------------------------------------------------------------------

    async def arun(
        self,
        prompt: str,
        user_id: str = "default",
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Route the task to the appropriate sub-agent, then optionally
        synthesize the result using the general Gemini agent.
        """
        self._state = AgentLifecycleState.RUNNING
        task_type = _classify_task(prompt)
        logger.info(
            "[ADKOrchestrator] Task classified as '%s' for prompt: %.80s...",
            task_type, prompt,
        )

        try:
            if task_type == "code":
                sub_result = await self._code_agent.arun(
                    prompt, user_id=user_id, session_id=session_id
                )
            elif task_type == "research":
                sub_result = await self._research_agent.arun(
                    prompt, user_id=user_id, session_id=session_id
                )
            else:
                sub_result = await super().arun(
                    prompt, user_id=user_id, session_id=session_id
                )

            # Store orchestration trace in memory
            self._memory.append(MemoryEntry(role="user", content=prompt))
            self._memory.append(MemoryEntry(
                role="assistant",
                content=sub_result,
                metadata={"routed_to": task_type},
            ))

            self._state = AgentLifecycleState.IDLE
            return sub_result

        except Exception as exc:  # noqa: BLE001
            self._state = AgentLifecycleState.FAILED
            logger.exception("[ADKOrchestrator] Routing error: %s", exc)
            return f"[ADKOrchestratorAgent] Error: {exc}"

    def get_routing_stats(self) -> Dict[str, int]:
        """Return a count of how many tasks were routed to each sub-agent."""
        stats: Dict[str, int] = {"code": 0, "research": 0, "general": 0}
        for entry in self._memory:
            if entry.role == "assistant" and "routed_to" in entry.metadata:
                routed = entry.metadata["routed_to"]
                stats[routed] = stats.get(routed, 0) + 1
        return stats
