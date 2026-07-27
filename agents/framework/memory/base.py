"""
Base interface for agent memory systems — Pydantic-First.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMemory(ABC):
    """Abstract base class for all agent episodic and long-term memory providers."""

    @abstractmethod
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a message in the memory store."""
        pass

    @abstractmethod
    async def get_history(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve recent interaction history for a user."""
        pass

    @abstractmethod
    async def clear_memory(self, user_id: str) -> None:
        """Clear memory for a specific user ID."""
        pass

    @abstractmethod
    async def bulk_insert_history(
        self, user_id: str, history: List[Dict[str, Any]]
    ) -> None:
        """Insert multiple messages at once for state restoration."""
        pass

    async def count_messages(self, user_id: str) -> int:
        """Return total count of stored messages for user (default implementation)."""
        history = await self.get_history(user_id, limit=1000000)
        return len(history)

    async def close(self) -> None:
        """Clean up underlying connections or memory resources."""
        pass


