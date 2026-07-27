"""
OpenClaw SDK — Agent Layer.

Provides the AgentClient, communication models, inference engines,
observability tracing, scheduling, and the unified exception hierarchy.
"""

from __future__ import annotations

import sys
if "optimization_core.agents" not in sys.modules:
    sys.modules["optimization_core.agents"] = sys.modules[__name__]

from .framework.interfaces.client.client import AgentClient
from .framework.models import (
    AgentAction,
    AgentResponse,
    InferenceResult,
    AgentConfig,
    ToolExecutionResult,
    TelemetryEvent,
    TokenUsage,
    AgentStepTrace,
)
from .framework.exceptions import (
    TruthGPTError,
    InferenceError,
    EngineInferenceTimeout,
    ToolExecutionError,
    ToolValidationError,
    RegistryError,
    PluginLoadError,
    ConfigurationError,
    AgentMemoryError,
    MemoryPersistenceError,
    HandoffError,
    RoutingError,
    SwarmRoutingError,
    AgentTimeoutError,
    SecurityPolicyViolationError,
    AgentStateError,
)
from .framework.registry import (
    registry,
    ComponentRegistry,
    ToolRegistry,
)
from .framework.engines.engine_registry import (
    engine_registry,
    EngineRegistry,
)

# Compatibility mappings for legacy test modules expecting `agents.*`
import optimization_core.agents.framework.engines.engine_registry as _engine_registry_mod
import optimization_core.agents.framework.engines.engine_benchmark as _engine_benchmark_mod
sys.modules["agents"] = sys.modules[__name__]
sys.modules["agents.engine_registry"] = _engine_registry_mod
sys.modules["agents.framework.engines.engine_registry"] = _engine_registry_mod
sys.modules["agents.framework.engines.engine_benchmark"] = _engine_benchmark_mod
sys.modules["optimization_core.agents.engine_registry"] = _engine_registry_mod
sys.modules["optimization_core.agents.engine_benchmark"] = _engine_benchmark_mod


# Bind module to package attribute so getattr(agents, "engine_registry") returns the module
engine_registry = _engine_registry_mod





__all__ = [
    # Client
    "AgentClient",
    # Models
    "AgentAction",
    "AgentResponse",
    "InferenceResult",
    "AgentConfig",
    "ToolExecutionResult",
    "TelemetryEvent",
    "TokenUsage",
    "AgentStepTrace",
    # Exceptions
    "TruthGPTError",
    "InferenceError",
    "EngineInferenceTimeout",
    "ToolExecutionError",
    "ToolValidationError",
    "RegistryError",
    "PluginLoadError",
    "ConfigurationError",
    "AgentMemoryError",
    "MemoryPersistenceError",
    "HandoffError",
    "RoutingError",
    "SwarmRoutingError",
    "AgentTimeoutError",
    "SecurityPolicyViolationError",
    "AgentStateError",
    # Registries
    "registry",
    "ComponentRegistry",
    "ToolRegistry",
    "engine_registry",
    "EngineRegistry",
]


