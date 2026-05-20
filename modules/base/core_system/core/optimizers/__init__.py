"""
Core Optimizers
===============
Unified exports for all optimizers in the core directory.
"""

# Import base optimizers
from optimization_core.modules.optimizers.core.pytorch_optimizer_base import (
    PyTorchOptimizerBase,
)

# Unified factory function for core optimizers
def create_core_optimizer(
    optimizer_type: str = "pytorch",
    config: dict = None
):
    """
    Unified factory function to create core optimizers.
    
    Args:
        optimizer_type: Type of optimizer to create. Options:
            - "pytorch" - PyTorchOptimizerBase
        config: Optional configuration dictionary
    
    Returns:
        The requested optimizer instance
    """
    if config is None:
        config = {}
    
    optimizer_type = optimizer_type.lower()
    
    factory_map = {
        "pytorch": lambda cfg: PyTorchOptimizerBase(cfg),
    }
    
    if optimizer_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown core optimizer type: '{optimizer_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[optimizer_type]
    return factory(config)


# Registry of all available core optimizers
CORE_OPTIMIZER_REGISTRY = {
    "pytorch": {
        "class": PyTorchOptimizerBase,
        "module": "optimization_core.modules.optimizers.core.pytorch_optimizer_base",
    },
}


def list_available_core_optimizers() -> list:
    """List all available core optimizer types."""
    return list(CORE_OPTIMIZER_REGISTRY.keys())


def get_core_optimizer_info(optimizer_type: str) -> dict:
    """
    Get information about a specific core optimizer.
    
    Args:
        optimizer_type: Type of optimizer
    
    Returns:
        Dictionary with optimizer information
    """
    if optimizer_type not in CORE_OPTIMIZER_REGISTRY:
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")
    
    registry_entry = CORE_OPTIMIZER_REGISTRY[optimizer_type]
    return {
        "type": optimizer_type,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
    }


__all__ = [
    "PyTorchOptimizerBase",
    "create_core_optimizer",
    "CORE_OPTIMIZER_REGISTRY",
    "list_available_core_optimizers",
    "get_core_optimizer_info",
]
