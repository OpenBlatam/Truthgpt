"""
ADKGeminiAgent — General-purpose native Google ADK agent backed by Gemini 2.5 Pro.

This agent wraps Google ADK's LlmAgent and integrates with TruthGPT's
BaseAgent lifecycle (AgentLifecycleState, MemoryEntry, AgentStatus),
so it can be registered in the UnifiedAgentRegistry like any other domain agent.

Usage::

    agent = ADKGeminiAgent(
        name="truth-gemini",
        instruction="You are a helpful assistant that always cites sources.",
    )
    response = await agent.run("What is the capital of France?")
    print(response)
"""

from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict, List, Optional

from agents.framework.architectures.base_agent import (
    BaseAgent,
    AgentLifecycleState,
    AgentStatus,
    MemoryEntry,
)
from agents.domains.google_adk.adk_tools import get_adk_tools

logger = logging.getLogger(__name__)

_ADK_MODEL = "gemini-2.5-pro"


class ADKGeminiAgent(BaseAgent):
    """
    General-purpose Gemini 2.5 Pro agent powered by Google ADK.

    Supports:
    - Synchronous and async ``run()``
    - All built-in TruthGPT @adk_tool tools
    - TruthGPT memory/lifecycle protocol (BaseAgent)
    - Graceful degradation if google-adk is not installed
    """

    def __init__(
        self,
        name: str = "adk-gemini-agent",
        instruction: str = (
            "You are a highly capable AI assistant integrated into the TruthGPT "
            "platform. You have access to tools to search knowledge, execute code, "
            "and monitor system metrics. Always be precise, cite reasoning steps, "
            "and never fabricate information."
        ),
        model: str = _ADK_MODEL,
        extra_tools: Optional[List[Any]] = None,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, role="gemini-adk-general")
        self.instruction = instruction
        self.model = model
        self.extra_tools = extra_tools or []
        self._api_key = api_key
        self._adk_agent: Any = None
        self._runner: Any = None
        self._session_service: Any = None
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _build_adk_agent(self) -> None:
        """Lazily build the underlying google.adk LlmAgent."""
        if self._initialized:
            return

        try:
            from google.adk.agents import LlmAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            import google.generativeai as genai

            if self._api_key:
                genai.configure(api_key=self._api_key)

            tools = get_adk_tools() + self.extra_tools

            self._adk_agent = LlmAgent(
                name=self.name,
                model=self.model,
                instruction=self.instruction,
                tools=tools,
            )

            self._session_service = InMemorySessionService()
            self._runner = Runner(
                agent=self._adk_agent,
                app_name=f"truthgpt-{self.name}",
                session_service=self._session_service,
            )

            self._initialized = True
            self._state = AgentLifecycleState.IDLE
            logger.info(
                "[ADKGeminiAgent] Initialized '%s' with model=%s, tools=%d",
                self.name, self.model, len(tools),
            )

        except ImportError as exc:
            logger.error(
                "[ADKGeminiAgent] google-adk not installed. "
                "Run: pip install google-adk>=1.0.0\n%s", exc
            )
            self._state = AgentLifecycleState.FAILED

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, prompt: str, user_id: str = "default", **kwargs: Any) -> str:
        """
        Synchronous run — wraps the async version for convenience.

        Args:
            prompt:  The user's message / task description.
            user_id: Optional session user identifier.

        Returns:
            The agent's final text response.
        """
        return asyncio.run(self.arun(prompt, user_id=user_id, **kwargs))

    async def arun(
        self,
        prompt: str,
        user_id: str = "default",
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async run — executes the ADK agent and streams the final response.

        Args:
            prompt:     The user's message / task description.
            user_id:    Optional session user identifier.
            session_id: Optional existing session ID to resume.

        Returns:
            The agent's final text response as a string.
        """
        self._build_adk_agent()

        if self._state == AgentLifecycleState.FAILED:
            return "[ADKGeminiAgent] Unavailable — google-adk not installed."

        try:
            from google.adk.sessions import InMemorySessionService
            from google.genai import types as adk_types

            self._state = AgentLifecycleState.RUNNING
            sid = session_id or f"{user_id}-{self.name}"

            # Ensure session exists
            existing = await self._session_service.get_session(
                app_name=f"truthgpt-{self.name}",
                user_id=user_id,
                session_id=sid,
            )
            if not existing:
                await self._session_service.create_session(
                    app_name=f"truthgpt-{self.name}",
                    user_id=user_id,
                    session_id=sid,
                )

            content = adk_types.Content(
                role="user",
                parts=[adk_types.Part(text=prompt)],
            )

            final_response = ""
            async for event in self._runner.run_async(
                user_id=user_id,
                session_id=sid,
                new_message=content,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                        break

            # Store in TruthGPT memory
            self._memory.append(MemoryEntry(role="user", content=prompt))
            self._memory.append(MemoryEntry(role="assistant", content=final_response))

            self._state = AgentLifecycleState.IDLE
            return final_response

        except Exception as exc:  # noqa: BLE001
            self._state = AgentLifecycleState.FAILED
            logger.exception("[ADKGeminiAgent] Error during run: %s", exc)
            return f"[ADKGeminiAgent] Error: {exc}"

    # ------------------------------------------------------------------
    # BaseAgent abstract methods
    # ------------------------------------------------------------------

    def get_status(self) -> AgentStatus:
        return AgentStatus(
            name=self.name,
            role=self.role,
            state=self._state,
            memory_size=len(self._memory),
            is_active=self._state not in (
                AgentLifecycleState.FAILED,
                AgentLifecycleState.COMPLETED,
            ),
        )

    def reset(self) -> None:
        self._memory.clear()
        self._initialized = False
        self._adk_agent = None
        self._runner = None
        self._session_service = None
        self._state = AgentLifecycleState.UNINITIALIZED
        logger.info("[ADKGeminiAgent] '%s' reset.", self.name)
