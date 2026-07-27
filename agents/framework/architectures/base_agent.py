"""
OpenClaw Base Agent Interface — Pydantic-First Architecture.

Defines the foundational abstract class for ALL agents in the OpenClaw
ecosystem. Every specialized agent (RL, Marketing, CodeInterpreter, etc.)
MUST inherit from this class.
"""

from __future__ import annotations

import time
import logging
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from optimization_core.agents.framework.models import AgentResponse
from optimization_core.core.framework.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Value Objects & State Enums
# ---------------------------------------------------------------------------

class AgentLifecycleState(str, Enum):
    """Lifecycle state of an agent during execution."""
    UNINITIALIZED = "uninitialized"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class MemoryEntry(BaseModel):
    """A single typed entry in the agent's episodic memory."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="The message content")
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStatus(BaseModel):
    """Structured snapshot of an agent's current state."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    role: str
    state: AgentLifecycleState = AgentLifecycleState.IDLE
    memory_size: int = 0
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Base Agent Abstract Class
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    OpenClaw Base Agent Interface.

    Provides:
    - Typed episodic memory via ``MemoryEntry``
    - Structured status reporting via ``AgentStatus``
    - Lifecycle hook callbacks (``on_start``, ``on_finish``, ``on_error``)
    - Async context manager interface
    - Abstract ``process()`` contract for all subclasses
    """

    def __init__(self, name: str, role: str) -> None:
        self.name = name
        self.role = role
        self.memory: List[MemoryEntry] = []
        self.state: AgentLifecycleState = AgentLifecycleState.IDLE
        self._created_at: float = time.time()
        self._memory_lock = threading.Lock()

    async def __aenter__(self) -> BaseAgent:
        """Async context manager entry."""
        await self.on_start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with automated error/finish handling."""
        if exc_val is not None:
            await self.on_error(exc_val)
        else:
            await self.on_finish()

    @abstractmethod
    async def process(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a query and return a structured AgentResponse."""
        pass

    def set_state(self, new_state: AgentLifecycleState) -> None:
        """Validate and update the agent's lifecycle state."""
        from optimization_core.agents.framework.exceptions import AgentStateError
        
        # Valid state transition guards
        invalid_transitions = {
            AgentLifecycleState.FAILED: {AgentLifecycleState.RUNNING},
        }
        if self.state in invalid_transitions and new_state in invalid_transitions[self.state]:
            raise AgentStateError(
                f"Invalid lifecycle transition for agent '{self.name}': {self.state.value} -> {new_state.value}",
                metadata={"agent": self.name, "from_state": self.state.value, "to_state": new_state.value}
            )
            
        logger.debug("Agent [%s] lifecycle transition: %s -> %s", self.name, self.state.value, new_state.value)
        self.state = new_state

    # --- Lifecycle Hooks ---

    async def on_start(self) -> None:
        """Hook called when agent starts a session or context."""
        self.set_state(AgentLifecycleState.RUNNING)

    async def on_finish(self) -> None:
        """Hook called when agent completes processing successfully."""
        self.set_state(AgentLifecycleState.COMPLETED)

    async def on_error(self, error: Exception) -> None:
        """Hook called when an unhandled exception occurs."""
        self.set_state(AgentLifecycleState.FAILED)
        logger.error("Agent [%s] encountered error: %s", self.name, error)

    async def on_action(self, action_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Hook called before performing a specific agent action or tool call."""
        logger.debug("Agent [%s] executing action: %s", self.name, action_name)

    # --- Execution Controls ---

    def default_fallback(self) -> AgentResponse:
        """Default fallback response when an unhandled error occurs during process()."""
        return AgentResponse(
            content=f"Error: Agent '{self.name}' encountered an unhandled exception during processing.",
            action_type="error",
            status_code=500,
            metadata={"status": "failed", "agent_name": self.name, "recovery": "safe_process_fallback"}
        )

    async def safe_process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Executes process() safely with automated state management and fallback."""
        try:
            await self.on_start()
            response = await ErrorHandler.async_safe_execute(
                self.process,
                self.default_fallback,
                query,
                context=context
            )
            await self.on_finish()
            return response
        except Exception as e:
            await self.on_error(e)
            return self.default_fallback()

    # --- Memory & State Management ---

    def add_to_memory(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Append a typed MemoryEntry to the episodic buffer in a thread-safe manner."""
        with self._memory_lock:
            self.memory.append(MemoryEntry(role=role, content=content, metadata=metadata or {}))

    def get_memory(self) -> List[Dict[str, Any]]:
        """Return memory as a list of dicts (backward-compatible)."""
        with self._memory_lock:
            return [entry.model_dump() for entry in self.memory]

    def get_memory_entries(self) -> List[MemoryEntry]:
        """Return raw typed MemoryEntry list."""
        with self._memory_lock:
            return list(self.memory)

    def clear_memory(self) -> None:
        """Clear episodic memory buffer."""
        with self._memory_lock:
            self.memory.clear()

    def export_state(self) -> Dict[str, Any]:
        """Export agent state, config, and memory entries for serialization."""
        with self._memory_lock:
            return {
                "name": self.name,
                "role": self.role,
                "state": self.state.value,
                "created_at": self._created_at,
                "memory": [e.model_dump() for e in self.memory],
            }

    def import_state(self, state_dict: Dict[str, Any]) -> None:
        """Restore agent memory and lifecycle state from a serialized dict."""
        with self._memory_lock:
            if "state" in state_dict:
                try:
                    self.state = AgentLifecycleState(state_dict["state"])
                except ValueError:
                    pass
            if "memory" in state_dict and isinstance(state_dict["memory"], list):
                self.memory = [MemoryEntry(**item) for item in state_dict["memory"] if isinstance(item, dict)]

    def get_status(self) -> AgentStatus:
        """Return a Pydantic-validated status snapshot."""
        with self._memory_lock:
            mem_size = len(self.memory)
        return AgentStatus(
            name=self.name,
            role=self.role,
            state=self.state,
            memory_size=mem_size,
            is_active=self.state != AgentLifecycleState.FAILED,
            created_at=self._created_at,
        )


