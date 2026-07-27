"""
OpenClaw Messaging -- Base Adapter.

Abstract base class providing the unified messaging adapter interface.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from optimization_core.agents.framework.models import AgentResponse

logger = logging.getLogger(__name__)


class BaseMessagingAdapter(ABC):
    """
    Abstract base for messaging platform adapters (Telegram, WhatsApp, etc.).
    Unified under the Pydantic-first AgentResponse model.
    """

    def __init__(self, agent_client: Any) -> None:
        self.agent_client = agent_client

    @abstractmethod
    async def on_message(
        self,
        platform_user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Process an incoming message and return the agent's response.
        MUST return an AgentResponse object.
        """
        pass

    @abstractmethod
    async def send_response(
        self,
        platform_user_id: str,
        response: AgentResponse,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a response back to the user on the platform.
        """
        pass

    async def handle(
        self,
        platform_user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Full round-trip: receive a message, run the agent, send the reply.
        Wrapped in safe error handling to guarantee an AgentResponse is returned.
        """
        logger.info(
            "[%s] Message from %s: %s",
            self.__class__.__name__,
            platform_user_id,
            text[:80] if text else "",
        )
        
        try:
            response = await self.on_message(platform_user_id, text, metadata)
            await self.send_response(platform_user_id, response, metadata)
            return response
        except Exception as exc:
            logger.error("[%s] Failure processing message from %s: %s", self.__class__.__name__, platform_user_id, exc)
            err_response = AgentResponse.error(
                error_message=f"Error in {self.__class__.__name__}: {exc}",
                status_code=500,
                metadata={"platform_user_id": platform_user_id, "adapter": self.__class__.__name__}
            )
            try:
                await self.send_response(platform_user_id, err_response, metadata)
            except Exception as send_exc:
                logger.error("[%s] Failed sending error response: %s", self.__class__.__name__, send_exc)
            return err_response


