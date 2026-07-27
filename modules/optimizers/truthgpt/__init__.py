"""
TruthGPT-Specific Optimizers
=============================
Optimizers specifically designed for TruthGPT models.
"""
from typing import Dict, Any, List

# Try imports for optional components
try:
    from ...truthgpt_dynamo_optimizer import (
        TruthGPTDynamoOptimizer,
        TruthGPTDynamoLevel,
        TruthGPTDynamoResult,
    )
except ImportError:
    TruthGPTDynamoOptimizer = None
    TruthGPTDynamoLevel = None
    TruthGPTDynamoResult = None

try:
    from ...truthgpt_inductor_optimizer import (
        TruthGPTInductorOptimizer,
        TruthGPTInductorLevel,
        TruthGPTInductorResult,
    )
except ImportError:
    TruthGPTInductorOptimizer = None
    TruthGPTInductorLevel = None
    TruthGPTInductorResult = None

try:
    from ...truthgpt_quantization_optimizer import (
        TruthGPTQuantizationOptimizer,
        TruthGPTQuantizationLevel,
        TruthGPTQuantizationResult,
    )
except ImportError:
    TruthGPTQuantizationOptimizer = None
    TruthGPTQuantizationLevel = None
    TruthGPTQuantizationResult = None

try:
    from optimizers.supreme_truthgpt_optimizer import (
        SupremeTruthGPTOptimizer,
        SupremeOptimizationLevel,
        SupremeOptimizationResult,
    )
except ImportError:
    try:
        from ...supreme_truthgpt_optimizer import (
            SupremeTruthGPTOptimizer,
            SupremeOptimizationLevel,
            SupremeOptimizationResult,
        )
    except ImportError:
        SupremeTruthGPTOptimizer = None
        SupremeOptimizationLevel = None
        SupremeOptimizationResult = None

    SupremeOptimizationResult = None

try:
    from ..transformer.transformer_optimizer import TransformerOptimizer
except ImportError:
    TransformerOptimizer = None


def create_truthgpt_optimizer(optimizer_type: str = "supreme", config: Dict[str, Any] = None):
    """Unified factory function to create TruthGPT-specific optimizers."""
    if config is None:
        config = {}
    
    optimizer_type = optimizer_type.lower()
    
    factory_map = {
        "supreme": lambda cfg: SupremeTruthGPTOptimizer(cfg) if SupremeTruthGPTOptimizer else None,
        "transformer": lambda cfg: TransformerOptimizer(cfg) if TransformerOptimizer else None,
    }
    
    if optimizer_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown TruthGPT optimizer type: '{optimizer_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[optimizer_type]
    return factory(config)


TRUTHGPT_OPTIMIZERS_REGISTRY = {
    "supreme": {
        "class": SupremeTruthGPTOptimizer,
        "level_enum": SupremeOptimizationLevel,
        "result_class": SupremeOptimizationResult,
        "factory": lambda cfg: SupremeTruthGPTOptimizer(cfg) if SupremeTruthGPTOptimizer else None,
    },
    "transformer": {
        "class": TransformerOptimizer,
        "level_enum": None,
        "result_class": None,
        "factory": lambda cfg: TransformerOptimizer(cfg) if TransformerOptimizer else None,
    },
}


def list_truthgpt_optimizers() -> List[str]:
    """List all available TruthGPT optimizer types."""
    return list(TRUTHGPT_OPTIMIZERS_REGISTRY.keys())


def get_truthgpt_optimizer_info(optimizer_type: str) -> Dict[str, Any]:
    """Get information about a specific TruthGPT optimizer."""
    if optimizer_type not in TRUTHGPT_OPTIMIZERS_REGISTRY:
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")
    
    registry_entry = TRUTHGPT_OPTIMIZERS_REGISTRY[optimizer_type]
    return {
        "type": optimizer_type,
        "class": registry_entry["class"].__name__ if registry_entry["class"] else None,
        "level_enum": registry_entry["level_enum"].__name__ if registry_entry["level_enum"] else None,
        "result_class": registry_entry["result_class"].__name__ if registry_entry["result_class"] else None,
    }


__all__ = [
    "TruthGPTDynamoOptimizer",
    "TruthGPTDynamoLevel",
    "TruthGPTDynamoResult",
    "TruthGPTInductorOptimizer",
    "TruthGPTInductorLevel",
    "TruthGPTInductorResult",
    "TruthGPTQuantizationOptimizer",
    "TruthGPTQuantizationLevel",
    "TruthGPTQuantizationResult",
    "SupremeTruthGPTOptimizer",
    "SupremeOptimizationLevel",
    "SupremeOptimizationResult",
    "TransformerOptimizer",
    "create_truthgpt_optimizer",
    "list_truthgpt_optimizers",
    "get_truthgpt_optimizer_info",
    "TRUTHGPT_OPTIMIZERS_REGISTRY",
]
