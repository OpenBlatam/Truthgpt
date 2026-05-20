"""
Unified Adapters System
=======================
Centralized access to all adapter classes in optimization_core.
"""

# Import core adapters
from ..core.adapters.optimizer_adapter import (
    OptimizerAdapter,
    PyTorchOptimizerAdapter,
)

from ..core.adapters.data_adapter import (
    DataAdapter,
    HuggingFaceDataAdapter,
    JSONLDataAdapter,
)

from ..core.adapters.model_adapter import (
    ModelAdapter,
    HuggingFaceModelAdapter,
)

# Import edge adapters
try:
    from ..modules.edge.edge_inference_adapter import (
        EdgeInferenceAdapter,
    )
except ImportError:
    EdgeInferenceAdapter = None

# Import TruthGPT adapters
try:
    from ..utils.truthgpt_adapters import (
        TruthGPTAdapter,
    )
except ImportError:
    TruthGPTAdapter = None

try:
    from ..utils.enterprise_truthgpt_adapter import (
        EnterpriseTruthGPTAdapter,
    )
except ImportError:
    EnterpriseTruthGPTAdapter = None


# Unified adapter factory
def create_adapter(
    adapter_type: str = "optimizer",
    adapter_subtype: str = "pytorch",
    config: dict = None
):
    """
    Unified factory function to create adapters.
    
    Args:
        adapter_type: Type of adapter to create. Options:
            - "optimizer" - OptimizerAdapter
            - "data" - DataAdapter
            - "model" - ModelAdapter
            - "edge" - EdgeInferenceAdapter
            - "truthgpt" - TruthGPTAdapter
            - "enterprise" - EnterpriseTruthGPTAdapter
        adapter_subtype: Subtype of adapter (e.g., "pytorch", "huggingface", "jsonl")
        config: Optional configuration dictionary
    
    Returns:
        The requested adapter instance
    """
    if config is None:
        config = {}
    
    adapter_type = adapter_type.lower()
    adapter_subtype = adapter_subtype.lower()
    
    factory_map = {
        "optimizer": {
            "pytorch": lambda cfg: PyTorchOptimizerAdapter(**cfg),
        },
        "data": {
            "huggingface": lambda cfg: HuggingFaceDataAdapter(**cfg),
            "jsonl": lambda cfg: JSONLDataAdapter(**cfg),
        },
        "model": {
            "huggingface": lambda cfg: HuggingFaceModelAdapter(**cfg),
        },
        "edge": {
            "inference": lambda cfg: EdgeInferenceAdapter(**cfg) if EdgeInferenceAdapter else None,
        },
        "truthgpt": {
            "default": lambda cfg: TruthGPTAdapter(**cfg) if TruthGPTAdapter else None,
        },
        "enterprise": {
            "default": lambda cfg: EnterpriseTruthGPTAdapter(**cfg) if EnterpriseTruthGPTAdapter else None,
        },
    }
    
    if adapter_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown adapter type: '{adapter_type}'. "
            f"Available types: {available}"
        )
    
    subtype_map = factory_map[adapter_type]
    
    if adapter_subtype not in subtype_map:
        available = ", ".join(subtype_map.keys())
        raise ValueError(
            f"Unknown adapter subtype '{adapter_subtype}' for type '{adapter_type}'. "
            f"Available subtypes: {available}"
        )
    
    factory = subtype_map[adapter_subtype]
    adapter = factory(config)
    
    if adapter is None:
        raise ImportError(f"Adapter type '{adapter_type}' with subtype '{adapter_subtype}' is not available (module not found)")
    
    return adapter


# Registry of all available adapters
ADAPTER_REGISTRY = {
    "optimizer": {
        "pytorch": {
            "class": PyTorchOptimizerAdapter,
            "module": "core.adapters.optimizer_adapter",
            "description": "PyTorch optimizer adapter",
        },
    },
    "data": {
        "huggingface": {
            "class": HuggingFaceDataAdapter,
            "module": "core.adapters.data_adapter",
            "description": "HuggingFace data adapter",
        },
        "jsonl": {
            "class": JSONLDataAdapter,
            "module": "core.adapters.data_adapter",
            "description": "JSONL data adapter",
        },
    },
    "model": {
        "huggingface": {
            "class": HuggingFaceModelAdapter,
            "module": "core.adapters.model_adapter",
            "description": "HuggingFace model adapter",
        },
    },
    "edge": {
        "inference": {
            "class": EdgeInferenceAdapter,
            "module": "modules.edge.edge_inference_adapter",
            "description": "Edge inference adapter",
        },
    },
    "truthgpt": {
        "default": {
            "class": TruthGPTAdapter,
            "module": "utils.truthgpt_adapters",
            "description": "TruthGPT adapter",
        },
    },
    "enterprise": {
        "default": {
            "class": EnterpriseTruthGPTAdapter,
            "module": "utils.enterprise_truthgpt_adapter",
            "description": "Enterprise TruthGPT adapter",
        },
    },
}


def list_available_adapter_types() -> list:
    """List all available adapter types."""
    return list(ADAPTER_REGISTRY.keys())


def list_available_adapter_subtypes(adapter_type: str) -> list:
    """
    List all available subtypes for an adapter type.
    
    Args:
        adapter_type: Type of adapter
    
    Returns:
        List of available subtypes
    """
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    return list(ADAPTER_REGISTRY[adapter_type].keys())


def get_adapter_info(adapter_type: str, adapter_subtype: str = None) -> dict:
    """
    Get information about a specific adapter.
    
    Args:
        adapter_type: Type of adapter
        adapter_subtype: Optional subtype of adapter
    
    Returns:
        Dictionary with adapter information
    """
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    if adapter_subtype is None:
        # Return info for all subtypes
        subtypes = ADAPTER_REGISTRY[adapter_type]
        return {
            "type": adapter_type,
            "subtypes": {
                subtype: {
                    "class": info["class"].__name__ if info["class"] else None,
                    "module": info["module"],
                    "description": info["description"],
                }
                for subtype, info in subtypes.items()
            }
        }
    
    if adapter_subtype not in ADAPTER_REGISTRY[adapter_type]:
        raise ValueError(f"Unknown adapter subtype: {adapter_subtype}")
    
    registry_entry = ADAPTER_REGISTRY[adapter_type][adapter_subtype]
    
    if registry_entry["class"] is None:
        raise ImportError(f"Adapter type '{adapter_type}' with subtype '{adapter_subtype}' is not available (module not found)")
    
    return {
        "type": adapter_type,
        "subtype": adapter_subtype,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Optimizer adapters
    "OptimizerAdapter",
    "PyTorchOptimizerAdapter",
    # Data adapters
    "DataAdapter",
    "HuggingFaceDataAdapter",
    "JSONLDataAdapter",
    # Model adapters
    "ModelAdapter",
    "HuggingFaceModelAdapter",
    # Edge adapters
    "EdgeInferenceAdapter",
    # TruthGPT adapters
    "TruthGPTAdapter",
    "EnterpriseTruthGPTAdapter",
    # Unified factory
    "create_adapter",
    # Registry
    "ADAPTER_REGISTRY",
    "list_available_adapter_types",
    "list_available_adapter_subtypes",
    "get_adapter_info",
]

