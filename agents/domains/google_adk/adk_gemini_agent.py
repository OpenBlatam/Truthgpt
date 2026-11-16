"""
ADKGeminiAgent — General-purpose native Google ADK agent backed by Gemini 2.5 Pro.

This agent wraps Google ADK's ``LlmAgent`` and fully implements
TruthGPT's ``BaseAgent`` lifecycle contract:

- ``process()``  → abstract from BaseAgent, delegates to ADK runner
- ``arun()``     → inherited pipeline (observe → process → act)
- Memory         → thread-safe via ``add_to_memory()``
- State          → transitions via ``set_state()``

Usage::

    agent = ADKGeminiAgent(
        name="truth-gemini",
        instruction="You are a helpful assistant that always cites sources.",
    )
    response = await agent.process("What is the capital of France?")
"""

from __future__ import annotations

import logging
import time
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
_APP_PREFIX = "truthgpt"


class ADKGeminiAgent(BaseAgent):
    """
    General-purpose Gemini 2.5 Pro agent powered by Google ADK.

    Integrates with BaseAgent's lifecycle hooks, thread-safe memory,
    state machine, ``export_state`` / ``import_state``, and the
    ``safe_process`` error boundary.

    The underlying ADK ``LlmAgent`` is built lazily on first call to
    ``process()`` so instantiation never triggers network I/O.
    """

    def __init__(
        self,
        name: str = "adk-gemini-agent",
        role: str = "gemini-adk-general",
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
        super().__init__(name=name, role=role)
        self.instruction = instruction
        self.model = model
        self.extra_tools: List[Any] = extra_tools or []
        self._api_key = api_key

        # Lazily-initialised ADK internals
        self._adk_agent: Any = None
        self._runner: Any = None
        self._session_service: Any = None
        self._adk_available: Optional[bool] = None  # None = not yet checked

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def app_name(self) -> str:
        return f"{_APP_PREFIX}-{self.name}"

    @property
    def is_adk_available(self) -> bool:
        """Check (and cache) whether google-adk can be imported."""
        if self._adk_available is None:
            try:
                import google.adk  # noqa: F401
                self._adk_available = True
            except ImportError:
                self._adk_available = False
        return self._adk_available

    # ------------------------------------------------------------------
    # Lazy ADK bootstrap
    # ------------------------------------------------------------------

    def _ensure_adk_agent(self) -> bool:
        """Lazily build the underlying ADK ``LlmAgent`` + ``Runner``.

        Returns ``True`` if the agent is ready, ``False`` on ImportError.
        """
        if self._adk_agent is not None:
            return True

        try:
            from google.adk.agents import LlmAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            import google.generativeai as genai
        except ImportError as exc:
            logger.error(
                "[%s] google-adk not installed. "
                "Run: pip install google-adk>=1.0.0\n%s",
                self.name, exc,
            )
            self._adk_available = False
            return False

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
            app_name=self.app_name,
            session_service=self._session_service,
        )

        self._adk_available = True
        logger.info(
            "[%s] ADK agent ready — model=%s, tools=%d",
            self.name, self.model, len(tools),
        )
        return True

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    async def _ensure_session(self, user_id: str, session_id: str) -> None:
        """Create an ADK session if one does not already exist."""
        existing = await self._session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if not existing:
            await self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )

    # ------------------------------------------------------------------
    # BaseAgent abstract: process()
    # ------------------------------------------------------------------

    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute the ADK agent for *query* and return the response text.

        This is the abstract method required by ``BaseAgent``.  It is also
        called by ``safe_process()`` which wraps it with lifecycle hooks
        and error handling.

        Args:
            query:   The user's prompt / task.
            context: Optional dict with ``user_id`` and ``session_id``.

        Returns:
            A string with the agent's final response, or a dict with
            ``content`` and ``metadata`` keys.
        """
        ctx = context or {}
        user_id: str = ctx.get("user_id", "default")
        session_id: str = ctx.get("session_id", f"{user_id}-{self.name}")

        if not self._ensure_adk_agent():
            return self._fallback_response(
                "[ADKGeminiAgent] Unavailable — google-adk is not installed."
            )

        from google.genai import types as adk_types

        await self._ensure_session(user_id, session_id)

        content = adk_types.Content(
            role="user",
            parts=[adk_types.Part(text=query)],
        )

        final_text = ""
        started = time.monotonic()

        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text
                break

        elapsed = round(time.monotonic() - started, 3)

        # Thread-safe memory updates
        self.add_to_memory("user", query)
        self.add_to_memory("assistant", final_text, metadata={
            "model": self.model,
            "latency_s": elapsed,
        })

        return {
            "content": final_text,
            "metadata": {
                "agent": self.name,
                "model": self.model,
                "latency_s": elapsed,
            },
        }

    # ------------------------------------------------------------------
    # Convenience sync wrapper
    # ------------------------------------------------------------------

    def run_sync(self, prompt: str, **kwargs: Any) -> str:
        """Synchronous helper — creates its own event loop if none is running.

        Prefer ``await agent.arun(prompt)`` or ``await agent.process(prompt)``
        in async code.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.process(prompt, kwargs))
                return self._extract_text(future.result())
        return self._extract_text(asyncio.run(self.process(prompt, kwargs)))

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Tear down ADK internals and reset lifecycle state."""
        self.clear_memory()
        self._adk_agent = None
        self._runner = None
        self._session_service = None
        self._adk_available = None
        self.set_state(AgentLifecycleState.IDLE)
        logger.info("[%s] Reset complete.", self.name)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(result: Any) -> str:
        """Pull the response text out of a dict or return it as-is."""
        if isinstance(result, dict):
            return result.get("content", str(result))
        return str(result)

    @staticmethod
    def _fallback_response(message: str) -> Dict[str, Any]:
        return {
            "content": message,
            "metadata": {"status": "unavailable"},
        }
