"""
TruthGPT Optimization Core - Modular Architecture
==================================================
Unified, high-performance, modular core framework organized for maintainability,
scalability, and rapid execution.

Submodules:
- systems: Infrastructure systems (dynamic factory, event system, service registry, plugin system, module loader)
- optimizers: Core optimizer implementations and unified factory
- services: Service layer and modular microservices
- validation: Validation layer for models, data, and configurations
- composition: Component assembler and workflow builder
- adapters: Model, data, and optimizer adapters
- framework: High-level AI optimization framework and pipelines
- common_runtime: Core runtime, configurations, base interfaces, and unified exception hierarchy
- data: Caching mechanisms and data handling
- kernel: TruthGPT kernel orchestrator, event bus, and infrastructure services
- kernels: Backward-compatible shim pointing to kernel
- ops: Extreme, quantum, and ultra-fast optimization operators
- platform: Hardware and performance profiling analyzers
- lib: Best-in-class library managers and recommendation engines
- distributed_runtime: Distributed optimization coordination
- runtime_fallback: Realtime CPU/eager execution fallback
- util: Complementary, enhanced, and microservices utility optimizers
"""

from __future__ import annotations

import sys
import types
import importlib
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

# ---------------------------------------------------------------------------
# Register Package Aliases in sys.modules
# ---------------------------------------------------------------------------
sys.modules.setdefault("core", sys.modules[__name__])
sys.modules.setdefault("optimization_core.core", sys.modules[__name__])


class _LazyModuleProxy(types.ModuleType):
    """Transparent proxy module that loads the actual module on first attribute access."""

    def __init__(self, full_name: str, target_rel_path: str, shim_name: str, pkg: str = "core"):
        super().__init__(full_name)
        self.__name__ = full_name
        self._target_rel_path = target_rel_path
        self._shim_name = shim_name
        self._pkg = pkg
        self._loaded_module: Optional[types.ModuleType] = None
        self._lock = threading.RLock()

        # If the target corresponds to a subdirectory package, set __path__ so Python recognizes it as a package
        target_dir = Path(__file__).parent / shim_name
        if target_dir.is_dir():
            self.__path__ = [str(target_dir)]

    def _get_target_module(self) -> types.ModuleType:
        if self._loaded_module is None:
            with self._lock:
                if self._loaded_module is None:
                    core_alias = f"core.{self._shim_name}"
                    opt_alias = f"optimization_core.core.{self._shim_name}"
                    pkg_alias = f"{self._pkg}.{self._shim_name}"

                    sys.modules.pop(core_alias, None)
                    sys.modules.pop(opt_alias, None)
                    sys.modules.pop(pkg_alias, None)

                    target = importlib.import_module(self._target_rel_path, package=self._pkg)
                    self._loaded_module = target
                    self.__dict__.update(target.__dict__)
                    self.__file__ = getattr(target, "__file__", None)
                    self.__path__ = getattr(target, "__path__", None)
                    self.__doc__ = getattr(target, "__doc__", None)
                    self.__all__ = getattr(target, "__all__", None)

                    sys.modules[core_alias] = target
                    sys.modules[opt_alias] = target
                    sys.modules[pkg_alias] = target
        return self._loaded_module

    def __getattr__(self, item: str) -> Any:
        mod = self._get_target_module()
        return getattr(mod, item)

    def __dir__(self) -> List[str]:
        mod = self._get_target_module()
        return dir(mod)

    def __repr__(self) -> str:
        if self._loaded_module is not None:
            return repr(self._loaded_module)
        return f"<lazy_module_proxy '{self.__name__}' from '{self._target_rel_path}'>"


# ---------------------------------------------------------------------------
# Lazy Imports Mapping (Symbols & Submodules)
# ---------------------------------------------------------------------------

_CORE_SUBMODULE_MAP: Dict[str, str] = {
    "systems": ".systems",
    "optimizers": ".optimizers",
    "services": ".services",
    "adapters": ".adapters",
    "framework": ".framework",
    "validation": ".validation",
    "composition": ".composition",
    "common_runtime": ".common_runtime",
    "runtime": ".common_runtime",
    "data": ".data",
    "kernel": ".kernel",
    "kernels": ".kernels",
    "ops": ".ops",
    "platform": ".platform",
    "lib": ".lib",
    "distributed_runtime": ".distributed_runtime",
    "runtime_fallback": ".runtime_fallback",
    "util": ".util",
}

_ALL_SHIM_TARGETS: Dict[str, str] = {
    **_CORE_SUBMODULE_MAP,
    # Flat infrastructure access shims for backward compatibility
    "dynamic_factory": ".systems.dynamic_factory",
    "event_system": ".systems.event_system",
    "service_registry": ".systems.service_registry",
    "plugin_system": ".systems.plugin_system",
    "module_loader": ".systems.module_loader",
    "config": ".common_runtime.config",
    "exceptions": ".common_runtime.exceptions",
    "interfaces": ".common_runtime.interfaces",
}

# Register lazy proxy modules in sys.modules
for _shim_name, _shim_rel_path in _ALL_SHIM_TARGETS.items():
    _proxy_core = _LazyModuleProxy(f"core.{_shim_name}", _shim_rel_path, _shim_name, pkg="core")
    _proxy_opt = _LazyModuleProxy(f"optimization_core.core.{_shim_name}", _shim_rel_path, _shim_name, pkg="core")
    sys.modules[f"core.{_shim_name}"] = _proxy_core
    sys.modules[f"optimization_core.core.{_shim_name}"] = _proxy_opt
    sys.modules[f"{__name__}.{_shim_name}"] = _proxy_core


_CORE_SYMBOL_MAP: Dict[str, tuple[str, str]] = {
    # Configurations
    "ConfigManager": (".common_runtime.config", "ConfigManager"),
    "TruthGPTConfigManager": (".common_runtime.config", "TruthGPTConfigManager"),
    "ConfigurationManager": (".common_runtime.config", "ConfigurationManager"),
    "TrainerConfig": (".common_runtime.config", "TrainerConfig"),
    "TrainingConfig": (".common_runtime.config", "TrainingConfig"),
    "ModelConfig": (".common_runtime.config", "ModelConfig"),
    "DataConfig": (".common_runtime.config", "DataConfig"),
    "OptimizerConfig": (".common_runtime.config", "OptimizerConfig"),
    "OptimizationConfig": (".common_runtime.config", "OptimizationConfig"),
    "MonitoringConfig": (".common_runtime.config", "MonitoringConfig"),
    "PerformanceConfig": (".common_runtime.config", "PerformanceConfig"),
    "HardwareConfig": (".common_runtime.config", "HardwareConfig"),
    "CheckpointConfig": (".common_runtime.config", "CheckpointConfig"),
    "EMAConfig": (".common_runtime.config", "EMAConfig"),
    "ResumeConfig": (".common_runtime.config", "ResumeConfig"),
    "Environment": (".common_runtime.config", "Environment"),
    "ConfigSource": (".common_runtime.config", "ConfigSource"),
    "create_config_manager": (".common_runtime.config", "create_config_manager"),
    "config_context": (".common_runtime.config", "config_context"),

    # Exceptions
    "TruthGPTCoreError": (".common_runtime.exceptions", "TruthGPTCoreError"),
    "PluginError": (".common_runtime.exceptions", "PluginError"),
    "ServiceRegistryError": (".common_runtime.exceptions", "ServiceRegistryError"),
    "OptimizerExecutionError": (".common_runtime.exceptions", "OptimizerExecutionError"),
    "MicroserviceCommunicationError": (".common_runtime.exceptions", "MicroserviceCommunicationError"),
    "ConfigValidationError": (".common_runtime.exceptions", "ConfigValidationError"),
    "OptimizationCoreError": (".common_runtime.exceptions", "OptimizationCoreError"),
    "ValidationError": (".common_runtime.exceptions", "ValidationError"),
    "ConfigurationError": (".common_runtime.exceptions", "ConfigurationError"),
    "ResourceError": (".common_runtime.exceptions", "ResourceError"),
    "PerformanceError": (".common_runtime.exceptions", "PerformanceError"),
    "ModelError": (".common_runtime.exceptions", "ModelError"),
    "InferenceError": (".common_runtime.exceptions", "InferenceError"),
    "DataError": (".common_runtime.exceptions", "DataError"),
    "ConfigError": (".common_runtime.exceptions", "ConfigError"),
    "ErrorSeverity": (".common_runtime.exceptions", "ErrorSeverity"),

    # Interfaces
    "BaseTrainer": (".common_runtime.interfaces", "BaseTrainer"),
    "BaseEvaluator": (".common_runtime.interfaces", "BaseEvaluator"),
    "BaseModelManager": (".common_runtime.interfaces", "BaseModelManager"),
    "BaseDataLoader": (".common_runtime.interfaces", "BaseDataLoader"),
    "BaseCheckpointManager": (".common_runtime.interfaces", "BaseCheckpointManager"),

    # Systems Components (Direct exports)
    "DynamicFactory": (".systems.dynamic_factory", "DynamicFactory"),
    "factory": (".systems.dynamic_factory", "factory"),
    "register_component": (".systems.dynamic_factory", "register_component"),
    "create_factory": (".systems.dynamic_factory", "create_factory"),
    "EventEmitter": (".systems.event_system", "EventEmitter"),
    "EventType": (".systems.event_system", "EventType"),
    "Event": (".systems.event_system", "Event"),
    "get_event_emitter": (".systems.event_system", "get_event_emitter"),
    "emit_event": (".systems.event_system", "emit_event"),
    "on_event": (".systems.event_system", "on_event"),
    "ServiceRegistry": (".systems.service_registry", "ServiceRegistry"),
    "ServiceContainer": (".systems.service_registry", "ServiceContainer"),
    "register_service": (".systems.service_registry", "register_service"),
    "get_service": (".systems.service_registry", "get_service"),
    "Plugin": (".systems.plugin_system", "Plugin"),
    "PluginManager": (".systems.plugin_system", "PluginManager"),
    "get_plugin_manager": (".systems.plugin_system", "get_plugin_manager"),
    "ModuleLoader": (".systems.module_loader", "ModuleLoader"),
    "get_module_loader": (".systems.module_loader", "get_module_loader"),
    "lazy_load": (".systems.module_loader", "lazy_load"),

    # Composition
    "ComponentAssembler": (".composition.component_assembler", "ComponentAssembler"),
    "WorkflowBuilder": (".composition.workflow_builder", "WorkflowBuilder"),

    # Validation
    "Validator": (".validation.validator", "Validator"),
    "ModelValidator": (".validation.model_validator", "ModelValidator"),
    "DataValidator": (".validation.data_validator", "DataValidator"),
    "ConfigValidator": (".validation.config_validator", "ConfigValidator"),

    # Kernel
    "TruthGPTKernel": (".kernel.truthgpt_kernel", "TruthGPTKernel"),
    "get_kernel": (".kernel", "get_kernel"),
    "set_kernel": (".kernel", "set_kernel"),

    # Optimizers Factory
    "create_core_optimizer": (".optimizers", "create_core_optimizer"),
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """Thread-safe lazy import system for core submodules and symbols."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]

        # 1. Submodules resolution
        if name in _CORE_SUBMODULE_MAP:
            mod_path = _CORE_SUBMODULE_MAP[name]
            try:
                mod = importlib.import_module(mod_path, package=__name__)
                _import_cache[name] = mod
                globals()[name] = mod
                return mod
            except Exception as e:
                raise AttributeError(f"Failed to import core submodule '{name}' from '{mod_path}': {e}") from e

        # 2. Direct symbols resolution
        if name in _CORE_SYMBOL_MAP:
            mod_path, symbol_name = _CORE_SYMBOL_MAP[name]
            try:
                mod = importlib.import_module(mod_path, package=__name__)
                obj = getattr(mod, symbol_name)
                _import_cache[name] = obj
                globals()[name] = obj
                return obj
            except Exception as e:
                raise AttributeError(f"Failed to lazy load symbol '{name}' from '{mod_path}.{symbol_name}': {e}") from e

        available = sorted(list(_CORE_SUBMODULE_MAP.keys()) + list(_CORE_SYMBOL_MAP.keys()))[:12]
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Available attributes include: {', '.join(available)}..."
        )


def __dir__() -> List[str]:
    """Return all available symbols including lazy-loaded submodules."""
    return sorted(list(set(globals().keys()) | set(_CORE_SUBMODULE_MAP.keys()) | set(_CORE_SYMBOL_MAP.keys()) | set(__all__)))


def list_available_core_modules() -> List[str]:
    """List all available core submodules."""
    return [
        "systems", "optimizers", "ops", "util", "kernel", "kernels",
        "services", "adapters", "framework", "validation", "composition",
        "runtime", "common_runtime", "data", "platform", "lib",
        "distributed_runtime", "runtime_fallback",
    ]


_MODULE_METADATA: Dict[str, Dict[str, str]] = {
    "systems": {
        "description": "Infrastructure systems: DynamicFactory, EventEmitter, ServiceRegistry, PluginManager, ModuleLoader",
        "category": "infrastructure",
    },
    "optimizers": {
        "description": "Core optimizer implementations and unified factory: Base, Unified, Modern, Modular, PyTorch, Quantum, etc.",
        "category": "optimization",
    },
    "services": {
        "description": "Service layer and modular microservices architecture",
        "category": "services",
    },
    "adapters": {
        "description": "Model, data, and optimizer adapters for polymorphic execution",
        "category": "integration",
    },
    "framework": {
        "description": "High-level AI optimization pipelines, state managers, and calculators",
        "category": "framework",
    },
    "validation": {
        "description": "Validation layer for models, configurations, and data structures",
        "category": "validation",
    },
    "composition": {
        "description": "Component assembler and dynamic workflow builders",
        "category": "workflow",
    },
    "common_runtime": {
        "description": "Core runtime interfaces, unified exceptions, config manager, and metrics utilities",
        "category": "runtime",
    },
    "runtime": {
        "description": "Alias for common_runtime",
        "category": "runtime",
    },
    "data": {
        "description": "Data caching, pool managers, and caching utilities",
        "category": "data",
    },
    "kernel": {
        "description": "TruthGPT kernel orchestrator, production event bus, and service management",
        "category": "kernel",
    },
    "kernels": {
        "description": "Backward-compatible shim pointing to TruthGPT kernel and kernel services",
        "category": "kernel",
    },
    "ops": {
        "description": "Extreme, quantum, and ultra-fast optimization operators",
        "category": "operations",
    },
    "platform": {
        "description": "Hardware detection, profiling, and performance analyzers",
        "category": "platform",
    },
    "lib": {
        "description": "Best-in-class library managers, recommendations, and installation guides",
        "category": "libraries",
    },
    "distributed_runtime": {
        "description": "Distributed optimization coordination and cluster management",
        "category": "distributed",
    },
    "runtime_fallback": {
        "description": "Realtime CPU/eager execution fallback mechanisms",
        "category": "runtime",
    },
    "util": {
        "description": "Complementary, enhanced, and microservices utility optimizers",
        "category": "utilities",
    },
}


def get_core_module_info(module_name: str) -> Dict[str, Any]:
    """Get metadata and component information for a core submodule."""
    if module_name not in _CORE_SUBMODULE_MAP:
        raise KeyError(f"Unknown core module '{module_name}'. Available: {list_available_core_modules()}")
    meta = _MODULE_METADATA.get(module_name, {})
    return {
        "name": module_name,
        "import_path": f"core.{module_name}",
        "relative_path": _CORE_SUBMODULE_MAP[module_name],
        "description": meta.get("description", ""),
        "category": meta.get("category", "general"),
    }


__all__ = [
    # Metadata & Discovery
    "list_available_core_modules",
    "get_core_module_info",

    # Config
    "ConfigManager",
    "TruthGPTConfigManager",
    "ConfigurationManager",
    "TrainerConfig",
    "TrainingConfig",
    "ModelConfig",
    "DataConfig",
    "OptimizerConfig",
    "OptimizationConfig",
    "MonitoringConfig",
    "PerformanceConfig",
    "HardwareConfig",
    "CheckpointConfig",
    "EMAConfig",
    "ResumeConfig",
    "Environment",
    "ConfigSource",
    "create_config_manager",
    "config_context",

    # Exceptions
    "TruthGPTCoreError",
    "PluginError",
    "ServiceRegistryError",
    "OptimizerExecutionError",
    "MicroserviceCommunicationError",
    "ConfigValidationError",
    "OptimizationCoreError",
    "ValidationError",
    "ConfigurationError",
    "ResourceError",
    "PerformanceError",
    "ModelError",
    "InferenceError",
    "DataError",
    "ConfigError",
    "ErrorSeverity",

    # Interfaces
    "BaseTrainer",
    "BaseEvaluator",
    "BaseModelManager",
    "BaseDataLoader",
    "BaseCheckpointManager",

    # Systems
    "DynamicFactory",
    "factory",
    "register_component",
    "create_factory",
    "EventEmitter",
    "EventType",
    "Event",
    "get_event_emitter",
    "emit_event",
    "on_event",
    "ServiceRegistry",
    "ServiceContainer",
    "register_service",
    "get_service",
    "Plugin",
    "PluginManager",
    "get_plugin_manager",
    "ModuleLoader",
    "get_module_loader",
    "lazy_load",

    # Composition
    "ComponentAssembler",
    "WorkflowBuilder",

    # Validation
    "Validator",
    "ModelValidator",
    "DataValidator",
    "ConfigValidator",

    # Kernel
    "TruthGPTKernel",
    "get_kernel",
    "set_kernel",

    # Optimizers
    "create_core_optimizer",

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
]
