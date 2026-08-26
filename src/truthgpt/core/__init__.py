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
import importlib
import threading
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# Register Package Aliases in sys.modules
# ---------------------------------------------------------------------------
sys.modules.setdefault("truthgpt.core", sys.modules[__name__])
sys.modules.setdefault("src.truthgpt.core", sys.modules[__name__])


def _register_submodule_shims(name: str, module: Any) -> None:
    """Register *module* across all standard namespace prefixes."""
    sys.modules[f"{__name__}.{name}"] = module
    sys.modules[f"truthgpt.core.{name}"] = module
    sys.modules[f"src.truthgpt.core.{name}"] = module


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
                _register_submodule_shims(name, mod)
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


__all__ = [
    # Metadata & Discovery
    "list_available_core_modules",

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
