import sys

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["registries"] = _mod
    sys.modules["optimization_core.registries"] = _mod

try:
    from factories.registry import Registry
except Exception:
    try:
        from optimization_core.factories.registry import Registry
    except Exception:
        Registry = None

try:
    from registries.service_registry import (
        ServiceRegistry,
        ServiceContainer,
        register_service,
        get_service,
    )
except Exception:
    try:
        from .service_registry import (
            ServiceRegistry,
            ServiceContainer,
            register_service,
            get_service,
        )
    except Exception:
        ServiceRegistry = None
        ServiceContainer = None
        register_service = None
        get_service = None

try:
    from registries.optimization_registry import (
        OptimizationRegistry,
        OptimizationConfig,
        apply_optimizations,
        get_optimization_config,
        register_optimization,
        get_optimization_report,
        AdvancedOptimizationConfig,
        get_advanced_optimization_config,
        apply_advanced_optimizations,
        get_advanced_optimization_report,
        AdvancedOptimizationConfigV2,
        get_advanced_optimization_config_v2,
        apply_advanced_optimizations_v2,
        get_advanced_optimization_report_v2,
        CommitTrackerOptimizationRegistry,
    )
except Exception:
    try:
        from .optimization_registry import (
            OptimizationRegistry,
            OptimizationConfig,
            apply_optimizations,
            get_optimization_config,
            register_optimization,
            get_optimization_report,
            AdvancedOptimizationConfig,
            get_advanced_optimization_config,
            apply_advanced_optimizations,
            get_advanced_optimization_report,
            AdvancedOptimizationConfigV2,
            get_advanced_optimization_config_v2,
            apply_advanced_optimizations_v2,
            get_advanced_optimization_report_v2,
            CommitTrackerOptimizationRegistry,
        )
    except Exception:
        OptimizationRegistry = None
        OptimizationConfig = None
        apply_optimizations = None
        get_optimization_config = None
        register_optimization = None
        get_optimization_report = None
        AdvancedOptimizationConfig = None
        get_advanced_optimization_config = None
        apply_advanced_optimizations = None
        get_advanced_optimization_report = None
        AdvancedOptimizationConfigV2 = None
        get_advanced_optimization_config_v2 = None
        apply_advanced_optimizations_v2 = None
        get_advanced_optimization_report_v2 = None
        CommitTrackerOptimizationRegistry = None

get_advanced_optimizations = get_advanced_optimization_config
get_advanced_optimization_config_v2 = get_advanced_optimization_config_v2

try:
    from registries.dataset_registry import (
        DatasetRegistry,
        register_dataset,
        build_dataset,
        DATASET_BUILDERS,
    )
except Exception:
    try:
        from .dataset_registry import (
            DatasetRegistry,
            register_dataset,
            build_dataset,
            DATASET_BUILDERS,
        )
    except Exception:
        DatasetRegistry = None
        register_dataset = None
        build_dataset = None
        DATASET_BUILDERS = {}


def get_registry(registry_type: str = "optimization"):
    """
    Get a registry instance by type.

    Args:
        registry_type: Type of registry to get. Options:
            - "optimization" - OptimizationRegistry
            - "advanced_optimization" - Advanced optimization registry
            - "service" - ServiceRegistry
            - "factory" - Generic Registry
            - "dataset" - DatasetRegistry
            - "commit_tracker" - CommitTrackerOptimizationRegistry

    Returns:
        The requested registry instance
    """
    registry_type = registry_type.lower()

    registry_map = {
        "optimization": OptimizationRegistry,
        "advanced_optimization": lambda: AdvancedOptimizationConfig(),
        "service": ServiceRegistry,
        "factory": Registry,
        "dataset": DatasetRegistry,
        "commit_tracker": CommitTrackerOptimizationRegistry,
    }

    if registry_type not in registry_map:
        available = ", ".join(registry_map.keys())
        raise ValueError(
            f"Unknown registry type: '{registry_type}'. "
            f"Available types: {available}"
        )

    registry_class = registry_map[registry_type]

    if callable(registry_class) and not isinstance(registry_class, type):
        return registry_class()
    elif isinstance(registry_class, type):
        return registry_class()
    else:
        return registry_class


REGISTRY_REGISTRY = {
    "optimization": {
        "class": OptimizationRegistry,
        "module": "registries.optimization_registry",
        "description": "Main optimization registry for managing optimization techniques",
    },
    "advanced_optimization": {
        "class": AdvancedOptimizationConfig,
        "module": "registries.optimization_registry",
        "description": "Advanced optimization registry with enhanced features",
    },
    "service": {
        "class": ServiceRegistry,
        "module": "registries.service_registry",
        "description": "Service registry with dependency injection",
    },
    "factory": {
        "class": Registry,
        "module": "factories.registry",
        "description": "Generic factory registry",
    },
    "dataset": {
        "class": DatasetRegistry,
        "module": "registries.dataset_registry",
        "description": "Dataset registry for managing datasets",
    },
    "commit_tracker": {
        "class": CommitTrackerOptimizationRegistry,
        "module": "registries.optimization_registry",
        "description": "Commit tracker optimization registry",
    },
}


def list_available_registries() -> list:
    """List all available registry types."""
    return list(REGISTRY_REGISTRY.keys())


def get_registry_info(registry_type: str) -> dict:
    """Get information about a specific registry."""
    if registry_type not in REGISTRY_REGISTRY:
        raise ValueError(f"Unknown registry type: {registry_type}")

    registry_entry = REGISTRY_REGISTRY[registry_type]
    return {
        "type": registry_type,
        "class": getattr(registry_entry["class"], "__name__", str(registry_entry["class"])),
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    "Registry",
    "ServiceRegistry",
    "ServiceContainer",
    "register_service",
    "get_service",
    "OptimizationRegistry",
    "OptimizationConfig",
    "apply_optimizations",
    "get_optimization_config",
    "register_optimization",
    "get_optimization_report",
    "AdvancedOptimizationConfig",
    "get_advanced_optimization_config",
    "get_advanced_optimizations",
    "apply_advanced_optimizations",
    "get_advanced_optimization_report",
    "AdvancedOptimizationConfigV2",
    "get_advanced_optimization_config_v2",
    "apply_advanced_optimizations_v2",
    "get_advanced_optimization_report_v2",
    "DatasetRegistry",
    "register_dataset",
    "build_dataset",
    "DATASET_BUILDERS",
    "CommitTrackerOptimizationRegistry",
    "get_registry",
    "REGISTRY_REGISTRY",
    "list_available_registries",
    "get_registry_info",
]
