"""
TruthGPT Framework Subpackage — Core Agent Components.

Provides foundational agent architectures, execution models, exception hierarchies,
component/tool/engine registries, client interfaces, and observability tracing.

All public names are available via lazy import to break circular dependency chains
that arise when sub-modules (e.g. ``react_agent`` → ``client`` → ``orchestration``
→ ``domains`` → ``react_agent``) try to import each other during package
initialisation.
"""

from __future__ import annotations

import sys as _sys
from typing import Any as _Any

# Self-register under the "agents.framework" alias **before** any relative
# sub-package imports.  When `agents/__init__.py` does `from . import framework`,
# Python begins executing *this* file.  The relative imports below (e.g.
# `from .architectures.base_agent import …`) cause CPython to look up the
# parent module name "agents.framework" in `sys.modules`.  But `agents/__init__`
# hasn't finished its `from . import framework` yet, so `sys.modules` doesn't
# have that key → KeyError.  Registering early breaks the chicken-and-egg.
_sys.modules.setdefault("agents.framework", _sys.modules[__name__])

# ---------------------------------------------------------------------------
# Lazy-import mapping: name → (module_path_relative_to_this_package, name)
# ---------------------------------------------------------------------------
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Architectures
    "BaseAgent":           (".architectures.base_agent", "BaseAgent"),
    "AgentLifecycleState": (".architectures.base_agent", "AgentLifecycleState"),
    "MemoryEntry":         (".architectures.base_agent", "MemoryEntry"),
    "AgentStatus":         (".architectures.base_agent", "AgentStatus"),
    "ReActAgent":          (".architectures.react_agent", "ReActAgent"),
    "MultiUserReActAgent": (".architectures.react_agent", "MultiUserReActAgent"),
    # Models
    "AgentAction":         (".models", "AgentAction"),
    "AgentResponse":       (".models", "AgentResponse"),
    "InferenceResult":     (".models", "InferenceResult"),
    "AgentConfig":         (".models", "AgentConfig"),
    "ToolExecutionResult": (".models", "ToolExecutionResult"),
    "TelemetryEvent":      (".models", "TelemetryEvent"),
    "TokenUsage":          (".models", "TokenUsage"),
    "AgentStepTrace":      (".models", "AgentStepTrace"),
    # Exceptions
    "TruthGPTError":                (".exceptions", "TruthGPTError"),
    "InferenceError":               (".exceptions", "InferenceError"),
    "EngineInferenceTimeout":       (".exceptions", "EngineInferenceTimeout"),
    "ToolExecutionError":           (".exceptions", "ToolExecutionError"),
    "ToolValidationError":          (".exceptions", "ToolValidationError"),
    "RegistryError":                (".exceptions", "RegistryError"),
    "PluginLoadError":              (".exceptions", "PluginLoadError"),
    "ConfigurationError":           (".exceptions", "ConfigurationError"),
    "AgentMemoryError":             (".exceptions", "AgentMemoryError"),
    "MemoryPersistenceError":       (".exceptions", "MemoryPersistenceError"),
    "HandoffError":                 (".exceptions", "HandoffError"),
    "RoutingError":                 (".exceptions", "RoutingError"),
    "SwarmRoutingError":            (".exceptions", "SwarmRoutingError"),
    "AgentTimeoutError":            (".exceptions", "AgentTimeoutError"),
    "SecurityPolicyViolationError": (".exceptions", "SecurityPolicyViolationError"),
    "AgentStateError":              (".exceptions", "AgentStateError"),
    # Registries
    "registry":           (".registry", "registry"),
    "ComponentRegistry":  (".registry", "ComponentRegistry"),
    "ToolRegistry":       (".registry", "ToolRegistry"),
    "engine_registry":    (".engines.engine_registry", "engine_registry"),
    "EngineRegistry":     (".engines.engine_registry", "EngineRegistry"),
    # Interfaces
    "AgentClient":        (".interfaces.client.client", "AgentClient"),
}


def __getattr__(name: str) -> _Any:
    """Lazy-load public symbols on first access."""
    if name in _LAZY_IMPORTS:
        mod_path, attr = _LAZY_IMPORTS[name]
        import importlib
        mod = importlib.import_module(mod_path, package=__name__)
        value = getattr(mod, attr)
        # Cache in module namespace so subsequent lookups skip __getattr__
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_LAZY_IMPORTS.keys())
