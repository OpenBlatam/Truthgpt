"""
Unified Registry System for TruthGPT
====================================
Centralized access to all registry systems across the TruthGPT ecosystem.
"""

from typing import Dict, Any, List, Optional

# Factory Generic Registry
from ..factories.registry import Registry

# Service Registry
from ..core.service_registry import (
    ServiceRegistry,
    ServiceContainer,
    register_service,
    get_service,
)

# Optimization Registry
from ..utils.performance.optimization_registry import (
    OptimizationRegistry,
    OptimizationConfig,
    apply_optimizations,
    get_optimization_config,
    register_optimization,
    get_optimization_report,
)

# Advanced Optimization Registries
from ..optimizers.registries.advanced_optimization_registry import (
    AdvancedOptimizationConfig,
    get_advanced_optimizations,
    apply_advanced_optimizations,
    get_advanced_optimization_report,
)

from ..optimizers.registries.advanced_optimization_registry_v2 import (
    AdvancedOptimizationConfig as AdvancedOptimizationConfigV2,
    get_advanced_optimization_config as get_advanced_optimization_config_v2,
    apply_advanced_optimizations as apply_advanced_optimizations_v2,
    get_advanced_optimization_report as get_advanced_optimization_report_v2,
)

# Dataset Registry Wrapper
from ..factories.datasets import DATASETS

class DatasetRegistry:
    """Wrapper for dataset registry functions."""
    
    @staticmethod
    def register(name: str):
        """Register a dataset builder."""
        return DATASETS.register(name)
    
    @staticmethod
    def build(name: str, *args, **kwargs):
        """Build a dataset by name."""
        return DATASETS.build(name, *args, **kwargs)
    
    @staticmethod
    def list_available():
        """List all available dataset names."""
        return DATASETS.list_keys()


# Unified registry factory
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


# Registry of all available registries
REGISTRY_REGISTRY = {
    "optimization": {
        "class": OptimizationRegistry,
        "module": "truthgpt.utils.performance.optimization_registry",
        "description": "Main optimization registry for managing optimization techniques",
    },
    "advanced_optimization": {
        "class": AdvancedOptimizationConfig,
        "module": "truthgpt.optimizers.registries.advanced_optimization_registry",
        "description": "Advanced optimization registry with enhanced features",
    },
    "service": {
        "class": ServiceRegistry,
        "module": "truthgpt.core.service_registry",
        "description": "Service registry with dependency injection",
    },
    "factory": {
        "class": Registry,
        "module": "truthgpt.factories.registry",
        "description": "Generic factory registry",
    },
    "dataset": {
        "class": DatasetRegistry,
        "module": "truthgpt.factories.datasets",
        "description": "Dataset registry for managing datasets",
    },
}


def list_available_registries() -> List[str]:
    """List all available registry types."""
    return list(REGISTRY_REGISTRY.keys())


def get_registry_info(registry_type: str) -> Dict[str, Any]:
    """Get information about a specific registry."""
    if registry_type not in REGISTRY_REGISTRY:
        raise ValueError(f"Unknown registry type: {registry_type}")
    
    registry_entry = REGISTRY_REGISTRY[registry_type]
    return {
        "type": registry_type,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Generic registry
    "Registry",
    # Service registry
    "ServiceRegistry",
    "ServiceContainer",
    "register_service",
    "get_service",
    # Optimization registries
    "OptimizationRegistry",
    "OptimizationConfig",
    "apply_optimizations",
    "get_optimization_config",
    "register_optimization",
    "get_optimization_report",
    # Advanced optimization registries
    "AdvancedOptimizationConfig",
    "get_advanced_optimizations",
    "apply_advanced_optimizations",
    "get_advanced_optimization_report",
    "AdvancedOptimizationConfigV2",
    "get_advanced_optimization_config_v2",
    "apply_advanced_optimizations_v2",
    "get_advanced_optimization_report_v2",
    # Dataset registry
    "DatasetRegistry",
    # Unified factory
    "get_registry",
    # Registry registry
    "REGISTRY_REGISTRY",
    "list_available_registries",
    "get_registry_info",
]
