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
- interfaces: Base interfaces
"""
from __future__ import annotations

# Direct imports for backward compatibility
from .config import ConfigManager, TrainerConfig
from .interfaces import (
    BaseTrainer,
    BaseEvaluator,
    BaseModelManager,
    BaseDataLoader,
    BaseCheckpointManager,
)
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

# Lazy imports for organized submodules
_LAZY_IMPORTS = {
    'systems': '.systems',
    'optimizers': '.optimizers',
    'services': '.services',
    'adapters': '.adapters',
    'framework': '.framework',
    'validation': '.validation',
    'composition': '.composition',
    'runtime': '.common_runtime',
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
        module = __import__(module_path, fromlist=[name], level=1)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def list_available_core_modules() -> list[str]:
    """List all available core submodules."""
    return list(_LAZY_IMPORTS.keys())


# Backward compatible imports - import directly for immediate availability
from .service_registry import (
    ServiceRegistry,
    ServiceContainer,
    register_service,
    get_service,
)
from .event_system import (
    EventEmitter,
    EventType,
    Event,
    get_event_emitter,
    emit_event,
    on_event,
)
from .plugin_system import (
    Plugin,
    PluginManager,
    get_plugin_manager,
)
from .dynamic_factory import (
    DynamicFactory,
    factory,
    register_component,
    create_factory,
)
from .module_loader import (
    ModuleLoader,
    get_module_loader,
    lazy_load,
)

__all__ = [
    # Config
    "ConfigManager",
    "TrainerConfig",
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
    "services",
    "adapters",
    "framework",
    "validation",
    "composition",
    "runtime",
    "list_available_core_modules",
]
