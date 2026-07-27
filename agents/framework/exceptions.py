"""
Unified Exception Hierarchy for TruthGPT / OpenClaw — Pydantic-First.

Provides a complete, structured exception tree that covers all failure
domains: inference, tools, routing, handoffs, memory, security, and timeouts.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Optional


class ErrorCode:
    """Standardized error code identifiers across OpenClaw domains."""
    UNKNOWN = "UNKNOWN_ERROR"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    INFERENCE_TIMEOUT = "INFERENCE_TIMEOUT"
    ENGINE_UNAVAILABLE = "ENGINE_UNAVAILABLE"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_VALIDATION_ERROR = "TOOL_VALIDATION_ERROR"
    TOOL_TIMEOUT_ERROR = "TOOL_TIMEOUT_ERROR"
    REGISTRY_ERROR = "REGISTRY_ERROR"
    PLUGIN_LOAD_ERROR = "PLUGIN_LOAD_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    MEMORY_PERSISTENCE_ERROR = "MEMORY_PERSISTENCE_ERROR"
    HANDOFF_ERROR = "HANDOFF_ERROR"
    HANDOFF_CYCLE_DETECTED = "HANDOFF_CYCLE_DETECTED"
    ROUTING_ERROR = "ROUTING_ERROR"
    SWARM_ROUTING_ERROR = "SWARM_ROUTING_ERROR"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_EXECUTION_ERROR = "AGENT_EXECUTION_ERROR"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    INVALID_STATE = "INVALID_STATE"


class TruthGPTError(Exception):
    """
    Base exception for all TruthGPT / OpenClaw errors.
    
    Attributes:
        message: Human-readable error description.
        metadata: Arbitrary contextual data associated with the failure.
        error_code: Standardized error identifier string.
        category: High-level classification domain.
        remediation_hint: Suggested recovery or troubleshooting action.
        timestamp: Unix timestamp when exception was created.
        is_retryable: Whether this error is transient and can be retried automatically.
        trace_id: Optional trace ID for observability correlation.
        cause: Optional underlying exception causing this error.
    """

    def __init__(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        category: Optional[str] = None,
        remediation_hint: Optional[str] = None,
        is_retryable: bool = False,
        trace_id: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.metadata = dict(metadata or {})
        self.error_code = error_code or ErrorCode.UNKNOWN
        self.category = category or "general"
        self.remediation_hint = remediation_hint or ""
        self.timestamp = time.time()
        self.is_retryable = is_retryable
        self.trace_id = trace_id or str(uuid.uuid4())
        self.cause = cause
        if cause is not None and not getattr(self, "__cause__", None):
            self.__cause__ = cause

    @property
    def http_status_code(self) -> int:
        """Map exception category to standard HTTP status code."""
        status_map = {
            "security": 403,
            "configuration": 400,
            "registry": 404,
            "tools": 422,
            "inference": 502,
            "memory": 500,
            "orchestration": 500,
            "execution": 500,
            "lifecycle": 409,
        }
        return status_map.get(self.category, 500)

    def __str__(self) -> str:
        if self.remediation_hint:
            return f"[{self.error_code}] {self.message} (Hint: {self.remediation_hint})"
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} code={self.error_code} category={self.category} retryable={self.is_retryable} msg={self.message!r}>"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error details for telemetry and API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "category": self.category,
            "remediation_hint": self.remediation_hint,
            "is_retryable": self.is_retryable,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "http_status": self.http_status_code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TruthGPTError:
        """Recreate exception from serialized dictionary representation."""
        err = cls(
            message=data.get("message", "Unknown error"),
            metadata=data.get("metadata", {}),
            error_code=data.get("error_code"),
            category=data.get("category"),
            remediation_hint=data.get("remediation_hint"),
            is_retryable=data.get("is_retryable", False),
            trace_id=data.get("trace_id"),
        )
        if "timestamp" in data:
            err.timestamp = data["timestamp"]
        return err

    def to_json(self) -> str:
        """JSON representation of the exception."""
        return json.dumps(self.to_dict())

    def with_metadata(self, **kwargs: Any) -> TruthGPTError:
        """Attach additional metadata to the exception instance and return self."""
        self.metadata.update(kwargs)
        return self

    def with_context(self, **kwargs: Any) -> TruthGPTError:
        """Alias for with_metadata for contextual error enrichment."""
        return self.with_metadata(**kwargs)


# Framework base alias for backwards compatibility and framework specification
AgentFrameworkError = TruthGPTError


class InferenceError(TruthGPTError):
    """Raised when the LLM engine fails or returns invalid output."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="inference", **kwargs)


class EngineInferenceTimeout(InferenceError):
    """Raised when LLM inference execution exceeds allowed time budget."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="INFERENCE_TIMEOUT", is_retryable=True, **kwargs)


class EngineUnavailableError(InferenceError):
    """Raised when target LLM provider engine service is unreachable or uninitialized."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="ENGINE_UNAVAILABLE", is_retryable=True, **kwargs)


class ToolExecutionError(TruthGPTError):
    """Raised when a registered tool fails during execution."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="tools", **kwargs)


class ToolValidationError(ToolExecutionError):
    """Raised when tool inputs fail type/schema validation checks."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="TOOL_VALIDATION_ERROR", is_retryable=False, **kwargs)


class ToolExecutionTimeoutError(ToolExecutionError):
    """Raised when tool invocation runtime exceeds its configured deadline."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="TOOL_TIMEOUT_ERROR", is_retryable=True, **kwargs)


class RegistryError(TruthGPTError):
    """Raised when there is an issue with Tool or Agent registration."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="registry", **kwargs)


class PluginLoadError(RegistryError):
    """Raised when dynamic plugin initialization or lazy import fails."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="PLUGIN_LOAD_ERROR", **kwargs)


class ConfigurationError(TruthGPTError):
    """Raised when the AgentConfig is invalid or missing required parameters."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="configuration", **kwargs)


class AgentMemoryError(TruthGPTError):
    """Raised when episodic or vector memory operations fail."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="memory", **kwargs)


class MemoryPersistenceError(AgentMemoryError):
    """Raised when saving or loading persistent memory state fails."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="MEMORY_PERSISTENCE_ERROR", is_retryable=True, **kwargs)


class HandoffError(TruthGPTError):
    """Raised when an agent-to-agent handoff fails (target not found, depth exceeded)."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="orchestration", **kwargs)


class AgentHandoffCycleError(HandoffError):
    """Raised when handoff routing forms a cyclic loop between agents."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="HANDOFF_CYCLE_DETECTED", is_retryable=False, **kwargs)


class RoutingError(TruthGPTError):
    """Raised when the Swarm Router cannot determine a valid target agent."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="orchestration", **kwargs)


class SwarmRoutingError(RoutingError):
    """Raised when specialized swarm target routing encounters a dead end."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, error_code="SWARM_ROUTING_ERROR", **kwargs)


class AgentTimeoutError(TruthGPTError):
    """Raised when an agent operation exceeds the configured time limit."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="execution", error_code="AGENT_TIMEOUT", is_retryable=True, **kwargs)


class AgentExecutionError(TruthGPTError):
    """Raised when internal agent execution reasoning loop encounters an unhandled state failure."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="execution", error_code="AGENT_EXECUTION_ERROR", **kwargs)


class SecurityPolicyViolationError(TruthGPTError):
    """Raised when an action or tool execution violates safety sandbox policy."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="security", error_code="SECURITY_VIOLATION", is_retryable=False, **kwargs)


class AgentStateError(TruthGPTError):
    """Raised when an agent transitions into or operates from an invalid lifecycle state."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__(message, metadata=metadata, category="lifecycle", error_code="INVALID_STATE", **kwargs)
