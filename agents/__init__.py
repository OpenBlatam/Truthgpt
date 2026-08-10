"""
OpenClaw SDK — Agent Layer.

Provides the AgentClient, communication models, inference engines,
observability tracing, scheduling, unified agent registry, architectures,
domain agents, orchestration engines, and exception hierarchy.

All public symbols are lazy-loaded to avoid the circular-import chains
caused by ``OptimizationCoreMetaFinder`` + Python 3.14's strict
``_initializing`` re-import logic.
"""

from __future__ import annotations

import sys
from typing import Any as _Any

# ---------------------------------------------------------------------------
# Module aliasing — must happen before any sub-imports
# ---------------------------------------------------------------------------
if "optimization_core.agents" not in sys.modules:
    sys.modules["optimization_core.agents"] = sys.modules[__name__]
sys.modules.setdefault("agents", sys.modules[__name__])

# ---------------------------------------------------------------------------
# Lazy-import mapping
# ---------------------------------------------------------------------------
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Subpackages (returned as modules, not attributes)
    "framework":     (".framework", None),
    "domains":       (".domains", None),
    "orchestration": (".orchestration", None),
    # Architectures
    "BaseAgent":           (".framework.architectures.base_agent", "BaseAgent"),
    "AgentLifecycleState": (".framework.architectures.base_agent", "AgentLifecycleState"),
    "MemoryEntry":         (".framework.architectures.base_agent", "MemoryEntry"),
    "AgentStatus":         (".framework.architectures.base_agent", "AgentStatus"),
    "ReActAgent":          (".framework.architectures.react_agent", "ReActAgent"),
    "MultiUserReActAgent": (".framework.architectures.react_agent", "MultiUserReActAgent"),
    # Client
    "AgentClient":         (".framework.interfaces.client.client", "AgentClient"),
    # Models
    "AgentAction":         (".framework.models", "AgentAction"),
    "AgentResponse":       (".framework.models", "AgentResponse"),
    "InferenceResult":     (".framework.models", "InferenceResult"),
    "AgentConfig":         (".framework.models", "AgentConfig"),
    "ToolExecutionResult": (".framework.models", "ToolExecutionResult"),
    "TelemetryEvent":      (".framework.models", "TelemetryEvent"),
    "TokenUsage":          (".framework.models", "TokenUsage"),
    "AgentStepTrace":      (".framework.models", "AgentStepTrace"),
    # Exceptions
    "TruthGPTError":                (".framework.exceptions", "TruthGPTError"),
    "InferenceError":               (".framework.exceptions", "InferenceError"),
    "EngineInferenceTimeout":       (".framework.exceptions", "EngineInferenceTimeout"),
    "ToolExecutionError":           (".framework.exceptions", "ToolExecutionError"),
    "ToolValidationError":          (".framework.exceptions", "ToolValidationError"),
    "RegistryError":                (".framework.exceptions", "RegistryError"),
    "PluginLoadError":              (".framework.exceptions", "PluginLoadError"),
    "ConfigurationError":           (".framework.exceptions", "ConfigurationError"),
    "AgentMemoryError":             (".framework.exceptions", "AgentMemoryError"),
    "MemoryPersistenceError":       (".framework.exceptions", "MemoryPersistenceError"),
    "HandoffError":                 (".framework.exceptions", "HandoffError"),
    "RoutingError":                 (".framework.exceptions", "RoutingError"),
    "SwarmRoutingError":            (".framework.exceptions", "SwarmRoutingError"),
    "AgentTimeoutError":            (".framework.exceptions", "AgentTimeoutError"),
    "SecurityPolicyViolationError": (".framework.exceptions", "SecurityPolicyViolationError"),
    "AgentStateError":              (".framework.exceptions", "AgentStateError"),
    # Registries
    "registry":          (".framework.registry", "registry"),
    "ComponentRegistry": (".framework.registry", "ComponentRegistry"),
    "ToolRegistry":      (".framework.registry", "ToolRegistry"),
    "engine_registry":   (".framework.engines.engine_registry", "engine_registry"),
    "EngineRegistry":    (".framework.engines.engine_registry", "EngineRegistry"),
    # Unified agent registry
    "AgentRegistry": (".unified_agent_registry", "AgentRegistry"),
    "agent_registry": (".unified_agent_registry", "agent_registry"),
}


def __getattr__(name: str) -> _Any:
    """Lazy-load public symbols on first access."""
    if name in _LAZY_IMPORTS:
        import importlib
        mod_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(mod_path, package=__name__)
        if attr is None:
            value = mod  # subpackage
        else:
            value = getattr(mod, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _setup_compat_aliases() -> None:
    """Register compatibility aliases for legacy ``agents.*`` imports.

    Called lazily the first time a downstream module triggers a full import
    of the agents package.  This avoids the circular chains that plagued
    the old eager registration.
    """
    import importlib
    try:
        _engine_registry_mod = importlib.import_module(
            ".framework.engines.engine_registry", package=__name__
        )
        _engine_benchmark_mod = importlib.import_module(
            ".framework.engines.engine_benchmark", package=__name__
        )
    except ImportError:
        return

    sys.modules["agents"] = sys.modules[__name__]
    sys.modules["agents.engine_registry"] = _engine_registry_mod
    sys.modules["agents.framework.engines.engine_registry"] = _engine_registry_mod
    sys.modules["agents.framework.engines.engine_benchmark"] = _engine_benchmark_mod
    sys.modules["optimization_core.agents.engine_registry"] = _engine_registry_mod
    sys.modules["optimization_core.agents.engine_benchmark"] = _engine_benchmark_mod


__all__ = list(_LAZY_IMPORTS.keys())
