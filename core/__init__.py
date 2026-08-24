"""
Core modules for modular architecture.

This module provides organized access to core components:
- systems: Infrastructure systems (factory, events, services, plugins, module loader)
- optimizers: Core optimizers
- services: Service implementations
- validation: Validation components
- composition: Composition and workflow builders
- adapters: Adapter components
- framework: Framework components
- common_runtime: Core runtime, configurations, interfaces, and exceptions
- data: Caching and data management
- kernel: TruthGPT kernel orchestrator and services
"""
from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Register this package under common import aliases so that downstream code
# can use `import core` or `import optimization_core.core` interchangeably.
# ---------------------------------------------------------------------------
sys.modules.setdefault("core", sys.modules[__name__])
sys.modules.setdefault("optimization_core.core", sys.modules[__name__])


# ---------------------------------------------------------------------------
# Helper: register a sub-module under all three namespace prefixes.
# ---------------------------------------------------------------------------
def _register_shim(name: str, module) -> None:
    """Register *module* so it is importable via multiple paths."""
    sys.modules[f"{__name__}.{name}"] = module
    sys.modules[f"core.{name}"] = module
    sys.modules[f"optimization_core.core.{name}"] = module


# ---------------------------------------------------------------------------
# Core common_runtime imports (eagerly loaded — they are small & always used)
# ---------------------------------------------------------------------------
try:
    from .common_runtime.config import ConfigManager, TrainerConfig, ModelConfig, DataConfig, OptimizerConfig
except ImportError:
    from .common_runtime.config import ConfigManager, TrainerConfig, ModelConfig, DataConfig  # type: ignore
    OptimizerConfig = None  # type: ignore

try:
    from .common_runtime.interfaces import (
        BaseTrainer,
        BaseEvaluator,
        BaseModelManager,
        BaseDataLoader,
        BaseCheckpointManager,
    )
except ImportError:
    BaseTrainer = None  # type: ignore
    BaseEvaluator = None  # type: ignore
    BaseModelManager = None  # type: ignore
    BaseDataLoader = None  # type: ignore
    BaseCheckpointManager = None  # type: ignore

from .composition import (
    ComponentAssembler,
    WorkflowBuilder,
)
from .validation import (
    Validator,
    ModelValidator,
    DataValidator,
    ConfigValidator,
)
from .common_runtime.exceptions import (
    TruthGPTCoreError,
    PluginError,
    ServiceRegistryError,
    OptimizerExecutionError,
    MicroserviceCommunicationError,
    ConfigValidationError,
    OptimizationCoreError,
)

# Core infrastructure systems imports
from .systems.service_registry import (
    ServiceRegistry,
    ServiceContainer,
    register_service,
    get_service,
)
from .systems.event_system import (
    EventEmitter,
    EventType,
    Event,
    get_event_emitter,
    emit_event,
    on_event,
)
from .systems.plugin_system import (
    Plugin,
    PluginManager,
    get_plugin_manager,
)
from .systems.dynamic_factory import (
    DynamicFactory,
    factory,
    register_component,
    create_factory,
)
from .systems.module_loader import (
    ModuleLoader,
    get_module_loader,
    lazy_load,
)

# ---------------------------------------------------------------------------
# Register all sub-packages under their shim aliases.
# Each sub-package is imported once and registered under all three prefixes.
# ---------------------------------------------------------------------------
from .systems import dynamic_factory as _df, event_system as _es, service_registry as _sr, plugin_system as _ps, module_loader as _ml
from .common_runtime import config as _cfg, exceptions as _exc, interfaces as _if

# Suppress the deprecation warning from kernels/ during our own package init
import warnings as _warnings
with _warnings.catch_warnings():
    _warnings.simplefilter("ignore", DeprecationWarning)
    from . import kernels as _kernels

from . import (
    kernel as _kernel,
    ops as _ops,
    util as _util,
    platform as _platform,
    lib as _lib,
    distributed_runtime as _dist_rt,
    runtime_fallback as _rt_fb,
    adapters as _adapters,
    composition as _composition,
    data as _data,
    framework as _framework,
    optimizers as _optimizers,
    services as _services,
    systems as _systems,
    validation as _validation,
)



# Map of shim-name → module for the triple-path registration
_shims = {
    # Infrastructure sub-modules (flat access from core.X)
    "dynamic_factory": _df,
    "event_system": _es,
    "service_registry": _sr,
    "plugin_system": _ps,
    "module_loader": _ml,
    "config": _cfg,
    "exceptions": _exc,
    "interfaces": _if,
    # Sub-packages
    "kernel": _kernel,
    "kernels": _kernels,   # backward compat — canonical is kernel
    "ops": _ops,
    "util": _util,
    "platform": _platform,
    "lib": _lib,
    "distributed_runtime": _dist_rt,
    "runtime_fallback": _rt_fb,
    "adapters": _adapters,
    "composition": _composition,
    "data": _data,
    "framework": _framework,
    "optimizers": _optimizers,
    "services": _services,
    "systems": _systems,
    "validation": _validation,
}

for _mod_name, _mod_obj in _shims.items():
    _register_shim(_mod_name, _mod_obj)


# ---------------------------------------------------------------------------
# Lazy import fallback — only fires for attributes not already in the
# module namespace (i.e., anything not eagerly imported above).
# ---------------------------------------------------------------------------
_LAZY_IMPORTS = {
    'runtime': '.common_runtime',
    'common_runtime': '.common_runtime',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for core submodules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name in _import_cache:
        return _import_cache[name]

    module_path = _LAZY_IMPORTS[name]
    try:
        import importlib
        module = importlib.import_module(module_path, package=__name__)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def list_available_core_modules() -> list[str]:
    """List all available core submodules."""
    # Return the same set as before for backward compat
    return [
        "systems", "optimizers", "ops", "util", "kernel", "kernels",
        "services", "adapters", "framework", "validation", "composition",
        "runtime", "common_runtime", "data", "platform", "lib",
        "distributed_runtime", "runtime_fallback",
    ]


__all__ = [
    # Config
    "ConfigManager",
    "TrainerConfig",
    "ModelConfig",
    "DataConfig",
    "OptimizerConfig",
    # Exceptions
    "TruthGPTCoreError",
    "PluginError",
    "ServiceRegistryError",
    "OptimizerExecutionError",
    "MicroserviceCommunicationError",
    "ConfigValidationError",
    "OptimizationCoreError",
    # Interfaces
    "BaseTrainer",
    "BaseEvaluator",
    "BaseModelManager",
    "BaseDataLoader",
    "BaseCheckpointManager",
    # Service Registry (backward compatible)
    "ServiceRegistry",
    "ServiceContainer",
    "register_service",
    "get_service",
    # Event System (backward compatible)
    "EventEmitter",
    "EventType",
    "Event",
    "get_event_emitter",
    "emit_event",
    "on_event",
    # Plugin System (backward compatible)
    "Plugin",
    "PluginManager",
    "get_plugin_manager",
    # Dynamic Factory (backward compatible)
    "DynamicFactory",
    "factory",
    "register_component",
    "create_factory",
    # Composition
    "ComponentAssembler",
    "WorkflowBuilder",
    # Validation
    "Validator",
    "ModelValidator",
    "DataValidator",
    "ConfigValidator",
    # Module Loader (backward compatible)
    "ModuleLoader",
    "get_module_loader",
    "lazy_load",
    # Submodules
    "systems",
    "optimizers",
    "ops",
    "util",
    "kernel",
    "kernels",
    "services",
    "adapters",
    "framework",
    "validation",
    "composition",
    "runtime",
    "common_runtime",
    "data",
    "platform",
    "lib",
    "distributed_runtime",
    "runtime_fallback",
    "list_available_core_modules",
]
