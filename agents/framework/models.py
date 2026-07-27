"""
Agent Communication Models — Pydantic-First Architecture.
System 5.9 Gold Standard — Hardened against trace-identified failure modes.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class AgentAction(BaseModel):
    """
    Universal model representing an LLM reasoning step, action invocation, or handoff.

    Attributes:
        thought: Optional private reasoning string.
        tool: Target tool identifier if executing a tool call.
        tool_input: Input parameters for the tool call.
        final_answer: Completed response text for the user.
        handoff: Target agent identifier if handing off execution.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    thought: Optional[str] = Field(
        None,
        description="Brief PRIVATE reasoning (not shown to the user). Never put the deliverable here."
    )
    tool: Optional[str] = Field(
        None,
        description="Name of the tool to call. Null if providing a final answer."
    )
    tool_input: Optional[Any] = Field(
        None,
        description="Arguments for the tool call (usually a string, dict, or primitive)."
    )
    final_answer: Optional[str] = Field(
        None,
        description="The complete, self-contained answer for the user. Required and non-empty whenever no tool/handoff is used."
    )
    handoff: Optional[str] = Field(
        None,
        description="Target agent name for a handoff transfer in a swarm/multi-agent architecture."
    )

    @field_validator("thought", "tool", "final_answer", "handoff", mode="before")
    @classmethod
    def clean_string_fields(cls, v: Any) -> Optional[str]:
        """Sanitize string values by stripping outer whitespace if string type."""
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v

    @field_validator("tool_input", mode="before")
    @classmethod
    def normalize_tool_input(cls, v: Any) -> Any:
        """
        HARDENED: Auto-convert dict tool_input to appropriate string/object format.
        """
        if isinstance(v, dict):
            if "query" in v and len(v) == 1:
                return str(v["query"])
            if "code" in v and len(v) == 1:
                return str(v["code"])
            if "path" in v and "content" in v and len(v) == 2:
                return f"{v['path']}:::{v['content']}"
            if "input" in v and len(v) == 1:
                return str(v["input"])
            if "url" in v and len(v) == 1:
                return str(v["url"])
            if "cmd" in v and len(v) == 1:
                return str(v["cmd"])
        return v

    @classmethod
    def parse_from_text(cls, text: str) -> AgentAction:
        """
        Robust JSON extraction from LLM output that may contain markdown blocks or trailing characters.
        """
        if not text or not text.strip():
            return cls(final_answer="[Empty LLM response received]")

        clean_text = text.strip()

        # 1. Look for ```json ... ``` code blocks first
        json_codeblock_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_text, re.DOTALL)
        if json_codeblock_match:
            try:
                return cls(**json.loads(json_codeblock_match.group(1)))
            except Exception:
                pass

        # 2. Find first '{' to last '}' to isolate standard JSON object
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return cls(**json.loads(json_str))
            except Exception:
                try:
                    sanitized = json_str.replace('\n', '\\n').replace('\r', '\\r')
                    return cls(**json.loads(sanitized))
                except Exception:
                    pass

        return cls(final_answer=clean_text)

    def is_final_answer(self) -> bool:
        """Return True if this action represents a completed response."""
        return bool(self.final_answer and not self.tool and not self.handoff)

    def is_tool_call(self) -> bool:
        """Return True if this action invokes a registered tool."""
        return bool(self.tool)

    def is_handoff(self) -> bool:
        """Return True if this action requests a swarm agent handoff."""
        return bool(self.handoff)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize action to dictionary representation."""
        return self.model_dump(exclude_none=True)

    def to_json(self) -> str:
        """Serialize action to JSON string."""
        return json.dumps(self.to_dict())

    def copy_with(self, **kwargs: Any) -> AgentAction:
        """Return an updated copy of the action."""
        data = self.model_dump()
        data.update(kwargs)
        return AgentAction(**data)

    @classmethod
    def create_tool_call(cls, tool: str, tool_input: Any, thought: Optional[str] = None) -> AgentAction:
        """Construct an AgentAction representing a tool invocation."""
        return cls(tool=tool, tool_input=tool_input, thought=thought)

    @classmethod
    def create_final_answer(cls, final_answer: str, thought: Optional[str] = None) -> AgentAction:
        """Construct an AgentAction representing a final response."""
        return cls(final_answer=final_answer, thought=thought)

    @classmethod
    def create_handoff(cls, target_agent: str, thought: Optional[str] = None) -> AgentAction:
        """Construct an AgentAction representing a swarm handoff request."""
        return cls(handoff=target_agent, thought=thought)


class AgentResponse(BaseModel):
    """Response from the agent orchestrator to the client."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: str = Field(..., description="Primary text response content.")
    action_type: str = Field("final_answer", description="'final_answer', 'handoff', 'approval_required', 'error'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata.")
    handoff_target: Optional[str] = Field(None, description="Target agent if action_type is 'handoff'.")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Audit log of tool calls executed.")
    execution_time_ms: Optional[float] = Field(None, description="Total execution duration in ms.")
    status_code: int = Field(200, description="HTTP-compatible status code (200 = OK, 500 = Error).")

    @property
    def is_success(self) -> bool:
        """Check if execution completed without error."""
        return self.status_code == 200 and self.action_type != "error"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize response object to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Serialize response object to JSON string."""
        return json.dumps(self.to_dict())

    def with_metadata(self, **kwargs: Any) -> AgentResponse:
        """Return a copy of response with additional metadata merged."""
        new_metadata = {**self.metadata, **kwargs}
        return self.model_copy(update={"metadata": new_metadata})

    @classmethod
    def success(
        cls,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> AgentResponse:
        """Construct a successful AgentResponse instance."""
        return cls(
            content=content,
            action_type="final_answer",
            status_code=200,
            metadata=metadata or {},
            tool_calls=tool_calls or [],
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def handoff(
        cls,
        target_agent: str,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> AgentResponse:
        """Construct a handoff AgentResponse instance."""
        return cls(
            content=content or f"Handing off to agent: {target_agent}",
            action_type="handoff",
            status_code=200,
            handoff_target=target_agent,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def error(
        cls,
        error_message: str,
        status_code: int = 500,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> AgentResponse:
        """Construct an error AgentResponse instance."""
        return cls(
            content=error_message,
            action_type="error",
            status_code=status_code,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
        )


class InferenceResult(BaseModel):
    """Unified model for LLM inference outputs."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str = Field(..., description="The generated text content.")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens produced.")
    latency_ms: Optional[float] = Field(None, description="Time taken for inference in milliseconds.")
    model_name: Optional[str] = Field(None, description="Name of the model that generated this.")
    finish_reason: Optional[str] = Field(None, description="Why the generation stopped.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize inference result to dictionary representation."""
        return self.model_dump()

    def to_json(self) -> str:
        """Serialize inference result to JSON string."""
        return json.dumps(self.to_dict())


class AgentConfig(BaseModel):
    """Configuration settings for AgentClient and agent instances."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm_engine: Optional[Any] = Field(None, description="Async callable LLM engine.")
    memory_db_path: str = Field("openclaw_memory.db", description="Path to SQLite memory database.")
    use_swarm: bool = Field(False, description="Enable multi-agent Swarm mode.")
    use_vector_memory: bool = Field(False, description="Enable vector search memory.")
    use_reflexion: bool = Field(False, description="Enable self-reflection loops.")
    max_handoff_depth: int = Field(5, description="Maximum allowed agent-to-agent transfers.")
    default_agent_name: Optional[str] = Field(None, description="Default primary agent name.")
    enable_telemetry: bool = Field(True, description="Enable OpenTelemetry tracing.")
    persistent: bool = Field(True, description="Enable Infinite Execution Persistence.")
    persistence_db_path: str = Field("agent_persistence.db", description="Path to persistence DB.")
    timeout_seconds: float = Field(120.0, description="Global execution timeout per agent query.")
    max_iterations: int = Field(60, description="Maximum ReAct reasoning iterations.")
    thought_verification_enabled: bool = Field(True, description="Enable thought verification checks.")

    @classmethod
    def from_env(cls) -> AgentConfig:
        """Create AgentConfig automatically populating values from environment variables."""
        import os
        return cls(
            memory_db_path=os.getenv("AGENT_MEMORY_DB_PATH", "openclaw_memory.db"),
            use_swarm=os.getenv("AGENT_USE_SWARM", "false").lower() in ("true", "1", "yes"),
            use_vector_memory=os.getenv("AGENT_USE_VECTOR_MEMORY", "false").lower() in ("true", "1", "yes"),
            use_reflexion=os.getenv("AGENT_USE_REFLEXION", "false").lower() in ("true", "1", "yes"),
            max_handoff_depth=int(os.getenv("AGENT_MAX_HANDOFF_DEPTH", "5")),
            default_agent_name=os.getenv("AGENT_DEFAULT_NAME", None),
            enable_telemetry=os.getenv("AGENT_ENABLE_TELEMETRY", "true").lower() in ("true", "1", "yes"),
            persistent=os.getenv("AGENT_PERSISTENT", "true").lower() in ("true", "1", "yes"),
            persistence_db_path=os.getenv("AGENT_PERSISTENCE_DB_PATH", "agent_persistence.db"),
            timeout_seconds=float(os.getenv("AGENT_TIMEOUT_SECONDS", "120.0")),
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "60")),
            thought_verification_enabled=os.getenv("AGENT_THOUGHT_VERIFICATION", "true").lower() in ("true", "1", "yes"),
        )

    def copy_with(self, **kwargs: Any) -> AgentConfig:
        """Return an updated copy of the configuration."""
        data = self.model_dump()
        data.update(kwargs)
        return AgentConfig(**data)

    @field_validator("max_handoff_depth")
    @classmethod
    def validate_handoff_depth(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_handoff_depth must be at least 1")
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("timeout_seconds must be positive")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent config to dictionary representation."""
        return self.model_dump(exclude_none=True)


class ToolExecutionResult(BaseModel):
    """Structured result wrapper for tool execution outputs."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_name: str = Field(..., description="Unique name of executed tool")
    success: bool = Field(..., description="Whether tool execution succeeded")
    output: Any = Field(None, description="Output payload from tool")
    error_message: Optional[str] = Field(None, description="Error details if execution failed")
    execution_time_ms: float = Field(0.0, description="Execution duration in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tool execution result to dictionary representation."""
        return self.model_dump()

    @classmethod
    def create_success(cls, tool_name: str, output: Any, execution_time_ms: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ToolExecutionResult:
        """Factory for successful tool execution result."""
        return cls(
            tool_name=tool_name,
            success=True,
            output=output,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
        )

    @classmethod
    def create_error(cls, tool_name: str, error_message: str, execution_time_ms: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ToolExecutionResult:
        """Factory for failed tool execution result."""
        return cls(
            tool_name=tool_name,
            success=False,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
        )


class TelemetryEvent(BaseModel):
    """Structured telemetry event envelope."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Category or event type identifier")
    agent_name: str = Field(..., description="Agent triggering the telemetry event")
    user_id: Optional[str] = Field(None, description="Optional associated user ID")
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize telemetry event to dictionary representation."""
        return self.model_dump()


class TokenUsage(BaseModel):
    """Token consumption and estimated financial cost metrics envelope."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    prompt_tokens: int = Field(0, description="Tokens used in prompt input")
    completion_tokens: int = Field(0, description="Tokens generated in output")
    total_tokens: int = Field(0, description="Total tokens consumed")
    estimated_cost_usd: float = Field(0.0, description="Estimated monetary cost in USD")

    @model_validator(mode="after")
    def compute_total_tokens(self) -> TokenUsage:
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        return self


class AgentStepTrace(BaseModel):
    """Detailed execution step trace record for multi-step agent reasoning loops."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    step_number: int = Field(..., description="1-indexed step sequence number")
    state: str = Field("THINKING", description="Lifecycle state (THINKING, ACTING, OBSERVING, FINISHED)")
    action: Optional[AgentAction] = Field(None, description="Action selected during step")
    observation: Optional[str] = Field(None, description="Observation or tool output payload")
    duration_ms: float = Field(0.0, description="Step duration in milliseconds")
    token_usage: Optional[TokenUsage] = Field(None, description="Tokens consumed during step")
    timestamp: float = Field(default_factory=time.time)

