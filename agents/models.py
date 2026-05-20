"""
Agent Communication Models.
System 5.9 Gold Standard — Hardened against trace-identified failure modes.
"""

import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AgentAction(BaseModel):
    """Universal model for an LLM reasoning step or action."""
    thought: Optional[str] = Field(None, description="Internal reasoning or thought process.")
    tool: Optional[str] = Field(None, description="Name of the tool to call. Null if providing a final answer.")
    tool_input: Optional[Any] = Field(None, description="Arguments for the tool call (usually a string or JSON).")
    final_answer: Optional[str] = Field(None, description="Final message to the user.")
    handoff: Optional[str] = Field(None, description="Target agent name for a handoff transfer.")

    @field_validator("tool_input", mode="before")
    @classmethod
    def normalize_tool_input(cls, v):
        """
        HARDENED (D7): Auto-convert dict tool_input to appropriate string format.
        
        The LLM frequently sends tool_input as a JSON dict instead of a string:
        - {"query": "open source AI..."} → "open source AI..."
        - {"code": "print('hello')"} → "print('hello')"
        - {"path": "/tmp/f.py", "content": "..."} → "/tmp/f.py:::..."
        
        This caused downstream format errors in traces 300100a1, 698e5908, ca34b516.
        """
        if isinstance(v, dict):
            # Common patterns: extract the meaningful string value
            if "query" in v:
                return str(v["query"])
            if "code" in v:
                return str(v["code"])
            if "path" in v and "content" in v:
                return f"{v['path']}:::{v['content']}"
            if "input" in v:
                return str(v["input"])
            if "url" in v:
                return str(v["url"])
            if "cmd" in v:
                return str(v["cmd"])
            # Fallback: serialize back to JSON string
            return json.dumps(v)
        return v

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """Override to ensure LLM-friendly descriptions."""
        schema = super().model_json_schema(*args, **kwargs)
        return schema

class AgentResponse(BaseModel):
    """Response from the agent orchestrator to the client."""
    content: str
    action_type: str  # 'final_answer', 'handoff', 'approval_required'
    metadata: Dict[str, Any] = Field(default_factory=dict)
    handoff_target: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

class InferenceResult(BaseModel):
    """Unified model for LLM inference outputs."""
    text: str = Field(..., description="The generated text content.")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens produced.")
    latency_ms: Optional[float] = Field(None, description="Time taken for inference in milliseconds.")
    model_name: Optional[str] = Field(None, description="Name of the model that generated this.")
    finish_reason: Optional[str] = Field(None, description="Why the generation stopped.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Configuration for the AgentClient."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm_engine: Optional[Any] = None
    memory_db_path: str = "openclaw_memory.db"
    use_swarm: bool = False
    use_vector_memory: bool = False
    use_reflexion: bool = False
    max_handoff_depth: int = 5
    default_agent_name: Optional[str] = None
    enable_telemetry: bool = True
    persistent: bool = True  # Enable Infinite Execution Persistence
    persistence_db_path: str = "agent_persistence.db"

