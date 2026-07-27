"""
OpenClaw Tool Base Abstractions — Pydantic-First Architecture.
"""

from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """
    Standardized result from a tool execution.
    Can contain the final output string and optional internal signals for the orchestrator.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    output: str = Field(..., description="The main text or output representation.")
    success: bool = Field(True, description="Whether tool execution succeeded.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with execution.")
    signal: Optional[str] = Field(None, description="Optional orchestrator signal (e.g., 'core_memory_append').")
    execution_time_ms: float = Field(0.0, description="Duration of tool execution in milliseconds.")


class BaseTool(ABC):
    """
    Base class for automated agent tools.
    Provides docstring-based description extraction, risk classification,
    and safe execution wrappers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for the tool."""
        pass

    @property
    def description(self) -> str:
        """Description extracted from class docstring for LLM system prompt consumption."""
        return self.__doc__.strip() if self.__doc__ else "No description available."

    @property
    def risk_level(self) -> str:
        """Risk classification level: 'LOW', 'MEDIUM', or 'HIGH'."""
        return "LOW"

    @property
    def requires_approval(self) -> bool:
        """If True, execution requires Human-In-The-Loop (HITL) approval."""
        return self.risk_level == "HIGH"

    @property
    def args_schema(self) -> Optional[Type[BaseModel]]:
        """Optional Pydantic BaseModel defining argument schema."""
        return None

    @abstractmethod
    async def run(self, arg: str) -> Any:
        """
        Asynchronous tool execution core method.
        May return a simple string or a typed ToolResult object.
        """
        pass

    async def safe_run(self, arg: str) -> ToolResult:
        """Execute run() safely with timing metrics and exception catching."""
        start_time = time.time()
        try:
            raw_res = await self.run(arg)
            duration = (time.time() - start_time) * 1000.0
            if isinstance(raw_res, ToolResult):
                raw_res.execution_time_ms = duration
                return raw_res
            return ToolResult(output=str(raw_res), success=True, execution_time_ms=duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000.0
            logger.error("Tool '%s' execution error: %s", self.name, e)
            return ToolResult(
                output=f"Error executing tool '{self.name}': {str(e)}",
                success=False,
                execution_time_ms=duration,
                metadata={"error": str(e)},
            )

