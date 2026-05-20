"""
Specialized Optimizers
======================
Optimizers for specific use cases and techniques.
"""

# Import specialized optimizers
from ..mcts_optimization import (
    MCTSOptimizer,
    MCTSOptimizationArgs,
    create_mcts_optimizer,
)

from ..enhanced_mcts_optimizer import (
    EnhancedMCTSWithBenchmarks,
    EnhancedMCTSBenchmarkArgs,
    create_enhanced_mcts_with_benchmarks,
    benchmark_mcts_comparison,
)

from ..enhanced_parameter_optimizer import (
    EnhancedParameterOptimizer,
    EnhancedParameterConfig,
    create_enhanced_parameter_optimizer,
    optimize_model_parameters,
)

from ..library_optimizer import (
    LibraryOptimizer,
)

from ..ai_extreme_optimizer import (
    AIExtremeOptimizer,
)

from ..extreme_speed_optimization_system import (
    ExtremeSpeedOptimizationSystem,
)

from ..pytorch_inspired_optimizer import (
    PyTorchInspiredOptimizer,
)


# Unified factory function for specialized optimizers
def create_specialized_optimizer(
    optimizer_type: str = "mcts",
    config: dict = None
):
    """
    Unified factory function to create specialized optimizers.
    
    Args:
        optimizer_type: Type of optimizer to create. Options:
            - "mcts" - MCTSOptimizer
            - "enhanced_mcts" - EnhancedMCTSWithBenchmarks
            - "parameter" - EnhancedParameterOptimizer
            - "library" - LibraryOptimizer
            - "ai_extreme" - AIExtremeOptimizer
            - "extreme_speed" - ExtremeSpeedOptimizationSystem
            - "pytorch_inspired" - PyTorchInspiredOptimizer
        config: Optional configuration dictionary
    
    Returns:
        The requested optimizer instance
    """
    if config is None:
        config = {}
    
    optimizer_type = optimizer_type.lower()
    
    factory_map = {
        "mcts": create_mcts_optimizer,
        "enhanced_mcts": create_enhanced_mcts_with_benchmarks,
        "parameter": create_enhanced_parameter_optimizer,
        "library": lambda cfg: LibraryOptimizer(cfg),
        "ai_extreme": lambda cfg: AIExtremeOptimizer(cfg),
        "extreme_speed": lambda cfg: ExtremeSpeedOptimizationSystem(cfg),
        "pytorch_inspired": lambda cfg: PyTorchInspiredOptimizer(cfg),
    }
    
    if optimizer_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown specialized optimizer type: '{optimizer_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[optimizer_type]
    return factory(config)


# Registry of all available specialized optimizers
SPECIALIZED_OPTIMIZER_REGISTRY = {
    "mcts": {
        "class": MCTSOptimizer,
        "factory": create_mcts_optimizer,
    },
    "enhanced_mcts": {
        "class": EnhancedMCTSWithBenchmarks,
        "factory": create_enhanced_mcts_with_benchmarks,
    },
    "parameter": {
        "class": EnhancedParameterOptimizer,
        "factory": create_enhanced_parameter_optimizer,
    },
    "library": {
        "class": LibraryOptimizer,
        "factory": lambda cfg: LibraryOptimizer(cfg),
    },
    "ai_extreme": {
        "class": AIExtremeOptimizer,
        "factory": lambda cfg: AIExtremeOptimizer(cfg),
    },
    "extreme_speed": {
        "class": ExtremeSpeedOptimizationSystem,
        "factory": lambda cfg: ExtremeSpeedOptimizationSystem(cfg),
    },
    "pytorch_inspired": {
        "class": PyTorchInspiredOptimizer,
        "factory": lambda cfg: PyTorchInspiredOptimizer(cfg),
    },
}


def list_available_specialized_optimizers() -> list:
    """List all available specialized optimizer types."""
    return list(SPECIALIZED_OPTIMIZER_REGISTRY.keys())


def get_specialized_optimizer_info(optimizer_type: str) -> dict:
    """
    Get information about a specific specialized optimizer.
    
    Args:
        optimizer_type: Type of optimizer
    
    Returns:
        Dictionary with optimizer information
    """
    if optimizer_type not in SPECIALIZED_OPTIMIZER_REGISTRY:
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")
    
    registry_entry = SPECIALIZED_OPTIMIZER_REGISTRY[optimizer_type]
    return {
        "type": optimizer_type,
        "class": registry_entry["class"].__name__,
        "factory": registry_entry["factory"].__name__ if hasattr(registry_entry["factory"], "__name__") else "lambda",
    }


__all__ = [
    # MCTS optimizers
    "MCTSOptimizer",
    "MCTSOptimizationArgs",
    "create_mcts_optimizer",
    "EnhancedMCTSWithBenchmarks",
    "EnhancedMCTSBenchmarkArgs",
    "create_enhanced_mcts_with_benchmarks",
    "benchmark_mcts_comparison",
    # Parameter optimizer
    "EnhancedParameterOptimizer",
    "EnhancedParameterConfig",
    "create_enhanced_parameter_optimizer",
    "optimize_model_parameters",
    # Other specialized optimizers
    "LibraryOptimizer",
    "AIExtremeOptimizer",
    "ExtremeSpeedOptimizationSystem",
    "PyTorchInspiredOptimizer",
    # Unified factory
    "create_specialized_optimizer",
    # Registry
    "SPECIALIZED_OPTIMIZER_REGISTRY",
    "list_available_specialized_optimizers",
    "get_specialized_optimizer_info",
]

