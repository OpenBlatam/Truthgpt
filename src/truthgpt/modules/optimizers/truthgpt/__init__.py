"""
TruthGPT-Specific Optimizers
=============================
Optimizers specifically designed for TruthGPT models.
"""

# Import TruthGPT-specific optimizers
    TruthGPTDynamoOptimizer,
    TruthGPTDynamoLevel,
    TruthGPTDynamoResult,
)

    TruthGPTInductorOptimizer,
    TruthGPTInductorLevel,
    TruthGPTInductorResult,
)

    TruthGPTQuantizationOptimizer,
    TruthGPTQuantizationLevel,
    TruthGPTQuantizationResult,
)

    SupremeTruthGPTOptimizer,
    SupremeOptimizationLevel,
    SupremeOptimizationResult,
)

from ..transformer.transformer_optimizer import (
    TransformerOptimizer,
)


# Unified factory function for TruthGPT optimizers
    optimizer_type: str = "dynamo",
    config: dict = None
):
    """
    Unified factory function to create TruthGPT-specific optimizers.
    
    Args:
        optimizer_type: Type of optimizer to create. Options:
            - "dynamo" - TruthGPTDynamoOptimizer
            - "inductor" - TruthGPTInductorOptimizer
            - "quantization" - TruthGPTQuantizationOptimizer
            - "supreme" - SupremeTruthGPTOptimizer
            - "transformer" - TransformerOptimizer
        config: Optional configuration dictionary
    
    Returns:
        The requested optimizer instance
    
    Example:
        >>> result = optimizer.optimize(model)
    """
    if config is None:
        config = {}
    
    optimizer_type = optimizer_type.lower()
    
    factory_map = {
        "supreme": lambda cfg: SupremeTruthGPTOptimizer(cfg),
        "transformer": lambda cfg: TransformerOptimizer(cfg),
    }
    
    if optimizer_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown TruthGPT optimizer type: '{optimizer_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[optimizer_type]
    return factory(config)


# Registry of all available TruthGPT optimizers
    "dynamo": {
        "class": TruthGPTDynamoOptimizer,
        "level_enum": TruthGPTDynamoLevel,
        "result_class": TruthGPTDynamoResult,
    },
    "inductor": {
        "class": TruthGPTInductorOptimizer,
        "level_enum": TruthGPTInductorLevel,
        "result_class": TruthGPTInductorResult,
    },
    "quantization": {
        "class": TruthGPTQuantizationOptimizer,
        "level_enum": TruthGPTQuantizationLevel,
        "result_class": TruthGPTQuantizationResult,
    },
    "supreme": {
        "class": SupremeTruthGPTOptimizer,
        "level_enum": SupremeOptimizationLevel,
        "result_class": SupremeOptimizationResult,
        "factory": lambda cfg: SupremeTruthGPTOptimizer(cfg),
    },
    "transformer": {
        "class": TransformerOptimizer,
        "level_enum": None,
        "result_class": None,
        "factory": lambda cfg: TransformerOptimizer(cfg),
    },
}


    """List all available TruthGPT optimizer types."""


    """
    Get information about a specific TruthGPT optimizer.
    
    Args:
        optimizer_type: Type of optimizer
    
    Returns:
        Dictionary with optimizer information
    """
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")
    
    return {
        "type": optimizer_type,
        "class": registry_entry["class"].__name__,
        "level_enum": registry_entry["level_enum"].__name__ if registry_entry["level_enum"] else None,
        "result_class": registry_entry["result_class"].__name__ if registry_entry["result_class"] else None,
        "factory": registry_entry["factory"].__name__ if hasattr(registry_entry["factory"], "__name__") else "lambda",
    }


__all__ = [
    # Dynamo optimizer
    "TruthGPTDynamoOptimizer",
    "TruthGPTDynamoLevel",
    "TruthGPTDynamoResult",
    # Inductor optimizer
    "TruthGPTInductorOptimizer",
    "TruthGPTInductorLevel",
    "TruthGPTInductorResult",
    # Quantization optimizer
    "TruthGPTQuantizationOptimizer",
    "TruthGPTQuantizationLevel",
    "TruthGPTQuantizationResult",
    # Supreme optimizer
    "SupremeTruthGPTOptimizer",
    "SupremeOptimizationLevel",
    "SupremeOptimizationResult",
    # Transformer optimizer
    "TransformerOptimizer",
    # Unified factory
    # Registry
]


