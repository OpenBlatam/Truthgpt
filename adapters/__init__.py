"""
Unified Adapters System
=======================
Centralized access to all adapter classes, exception types, protocols,
Pydantic result models, and factory utilities in optimization_core.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Type

from .base import (
    AdapterConfigurationError,
    AdapterError,
    AdapterExecutionError,
    AdapterRunResult,
    BaseAdapter,
    BaseAdapterProtocol,
    BaseDynamicAdapter,
    ObjectEntry,
    ObjectNotFoundError,
    ObjectStore,
    StoreStats,
)
from .data_adapter import (
    DataAdapter,
    DataInfoResult,
    DataListResult,
    DataLoadResult,
    DataSplitStats,
    HuggingFaceDataAdapter,
    JSONLDataAdapter,
)
from .model_adapter import (
    HuggingFaceModelAdapter,
    ModelAdapter,
    ModelInfoResult,
    ModelListResult,
    ModelLoadResult,
    ModelSaveResult,
)
from .optimizer_adapter import (
    OptimizerAdapter,
    OptimizerCreateResult,
    OptimizerListResult,
    OptimizerStateResult,
    PyTorchOptimizerAdapter,
)
from .training_adapter import (
    TrainingAdapter,
    TrainingCreateResult,
    TrainingRunResult,
)

# Placeholders for dynamic late binding
EdgeInferenceAdapter: Optional[Any] = None
TruthGPTAdapter: Optional[Any] = None
EnterpriseTruthGPTAdapter: Optional[Any] = None


# Import edge adapters
try:
    from ..modules.edge.edge_inference_adapter import EdgeInferenceAdapter
except (ImportError, ValueError):
    try:
        from modules.edge.edge_inference_adapter import EdgeInferenceAdapter
    except (ImportError, ValueError):
        EdgeInferenceAdapter = None

# Import TruthGPT adapters
try:
    from .truthgpt_adapters import TruthGPTAdapter
except (ImportError, ValueError):
    try:
        from ..utils.truthgpt_adapters import TruthGPTAdapter
    except (ImportError, ValueError):
        TruthGPTAdapter = None

try:
    from .enterprise_truthgpt_adapter import EnterpriseTruthGPTAdapter
except (ImportError, ValueError):
    try:
        from ..utils.enterprise_truthgpt_adapter import EnterpriseTruthGPTAdapter
    except (ImportError, ValueError):
        EnterpriseTruthGPTAdapter = None


# Unified adapter factory
def create_adapter(
    adapter_type: str = "optimizer",
    adapter_subtype: str = "pytorch",
    config: Optional[Dict[str, Any]] = None,
) -> BaseDynamicAdapter:
    """
    Unified factory function to instantiate adapter instances.

    Args:
        adapter_type: Type category of adapter to create. Options:
            - "optimizer" - PyTorchOptimizerAdapter
            - "data" - HuggingFaceDataAdapter / JSONLDataAdapter
            - "model" - HuggingFaceModelAdapter
            - "edge" - EdgeInferenceAdapter
            - "truthgpt" - TruthGPTAdapter
            - "enterprise" - EnterpriseTruthGPTAdapter
            - "training" - TrainingAdapter
        adapter_subtype: Subtype of adapter (e.g. "pytorch", "huggingface", "jsonl", "default", "inference")
        config: Optional configuration dictionary passed to adapter constructor.

    Returns:
        Instantiated BaseDynamicAdapter instance.

    Raises:
        ValueError: If adapter_type or adapter_subtype is unknown.
        ImportError: If requested adapter class is unavailable.
    """
    if config is None:
        config = {}

    adapter_type = adapter_type.lower()
    adapter_subtype = adapter_subtype.lower()

    # Subtype alias mappings for convenience
    subtype_aliases: Dict[str, str] = {
        "torch": "pytorch",
        "hf": "huggingface",
    }
    adapter_subtype = subtype_aliases.get(adapter_subtype, adapter_subtype)

    factory_map: Dict[str, Dict[str, Any]] = {
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
        "training": {
            "default": lambda cfg: TrainingAdapter(**cfg),
        },
    }

    if adapter_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown adapter type: '{adapter_type}'. Available types: {available}"
        )

    subtype_map = factory_map[adapter_type]

    if adapter_subtype not in subtype_map:
        available = ", ".join(subtype_map.keys())
        raise ValueError(
            f"Unknown adapter subtype '{adapter_subtype}' for type '{adapter_type}'. Available subtypes: {available}"
        )

    factory = subtype_map[adapter_subtype]
    adapter = factory(config)

    if adapter is None:
        raise ImportError(
            f"Adapter type '{adapter_type}' with subtype '{adapter_subtype}' is not available (module not found)"
        )

    return adapter


# Registry of all available adapters
ADAPTER_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "optimizer": {
        "pytorch": {
            "class": PyTorchOptimizerAdapter,
            "module": "optimization_core.adapters.optimizer_adapter",
            "description": "PyTorch optimizer adapter",
        },
    },
    "data": {
        "huggingface": {
            "class": HuggingFaceDataAdapter,
            "module": "optimization_core.adapters.data_adapter",
            "description": "HuggingFace data adapter",
        },
        "jsonl": {
            "class": JSONLDataAdapter,
            "module": "optimization_core.adapters.data_adapter",
            "description": "JSONL data adapter",
        },
    },
    "model": {
        "huggingface": {
            "class": HuggingFaceModelAdapter,
            "module": "optimization_core.adapters.model_adapter",
            "description": "HuggingFace model adapter",
        },
    },
    "training": {
        "default": {
            "class": TrainingAdapter,
            "module": "optimization_core.adapters.training_adapter",
            "description": "Training adapter",
        },
    },
    "edge": {
        "inference": {
            "class": EdgeInferenceAdapter,
            "module": "optimization_core.modules.edge.edge_inference_adapter",
            "description": "Edge inference adapter",
        },
    },
    "truthgpt": {
        "default": {
            "class": TruthGPTAdapter,
            "module": "optimization_core.adapters.truthgpt_adapters",
            "description": "TruthGPT adapter",
        },
    },
    "enterprise": {
        "default": {
            "class": EnterpriseTruthGPTAdapter,
            "module": "optimization_core.adapters.enterprise_truthgpt_adapter",
            "description": "Enterprise TruthGPT adapter",
        },
    },
}


def register_adapter(
    adapter_type: str,
    adapter_subtype: str,
    adapter_class: Type[BaseDynamicAdapter],
    module_path: str = "",
    description: str = "",
) -> None:
    """
    Register a custom dynamic adapter in the central ADAPTER_REGISTRY.

    Args:
        adapter_type: Classification string (e.g. 'custom_optimizer').
        adapter_subtype: Variant subtype handle (e.g. 'v1').
        adapter_class: Class inheriting from BaseDynamicAdapter.
        module_path: String path to module location.
        description: Informational description.
    """
    t_key = adapter_type.lower()
    st_key = adapter_subtype.lower()
    if t_key not in ADAPTER_REGISTRY:
        ADAPTER_REGISTRY[t_key] = {}
    ADAPTER_REGISTRY[t_key][st_key] = {
        "class": adapter_class,
        "module": module_path or adapter_class.__module__,
        "description": description or adapter_class.__doc__ or "Custom adapter",
    }


def list_available_adapter_types() -> List[str]:
    """List all available top-level adapter types registered in the system."""
    return list(ADAPTER_REGISTRY.keys())


def list_available_adapter_subtypes(adapter_type: str) -> List[str]:
    """
    List all available subtypes for a specific adapter type.

    Args:
        adapter_type: Category of adapter (e.g., 'optimizer', 'data', 'model')

    Returns:
        List of available subtype strings

    Raises:
        ValueError: If adapter_type is not registered
    """
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter type: {adapter_type}")

    return list(ADAPTER_REGISTRY[adapter_type].keys())


def get_adapter_info(adapter_type: str, adapter_subtype: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed information about registered adapter types or a specific subtype.

    Args:
        adapter_type: Category of adapter
        adapter_subtype: Optional specific subtype

    Returns:
        Dictionary containing metadata about the registered adapter(s)

    Raises:
        ValueError: If adapter_type or adapter_subtype is unknown
        ImportError: If the requested adapter class is not available
    """
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter type: {adapter_type}")

    if adapter_subtype is None:
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
            },
        }

    if adapter_subtype not in ADAPTER_REGISTRY[adapter_type]:
        raise ValueError(f"Unknown adapter subtype: {adapter_subtype}")

    registry_entry = ADAPTER_REGISTRY[adapter_type][adapter_subtype]

    if registry_entry["class"] is None:
        raise ImportError(
            f"Adapter type '{adapter_type}' with subtype '{adapter_subtype}' is not available (module not found)"
        )

    return {
        "type": adapter_type,
        "subtype": adapter_subtype,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Base
    "AdapterError",
    "ObjectNotFoundError",
    "AdapterConfigurationError",
    "AdapterExecutionError",
    "BaseAdapterProtocol",
    "BaseAdapter",
    "BaseDynamicAdapter",
    "ObjectStore",
    "ObjectEntry",
    "StoreStats",
    "AdapterRunResult",
    # Optimizer adapters
    "OptimizerAdapter",
    "PyTorchOptimizerAdapter",
    "OptimizerCreateResult",
    "OptimizerStateResult",
    "OptimizerListResult",
    # Data adapters
    "DataAdapter",
    "HuggingFaceDataAdapter",
    "JSONLDataAdapter",
    "DataSplitStats",
    "DataLoadResult",
    "DataInfoResult",
    "DataListResult",
    # Model adapters
    "ModelAdapter",
    "HuggingFaceModelAdapter",
    "ModelInfoResult",
    "ModelLoadResult",
    "ModelSaveResult",
    "ModelListResult",
    # Training adapters
    "TrainingAdapter",
    "TrainingCreateResult",
    "TrainingRunResult",
    # Edge adapters
    "EdgeInferenceAdapter",
    # TruthGPT adapters
    "TruthGPTAdapter",
    "EnterpriseTruthGPTAdapter",
    # Unified factory
    "create_adapter",
    "register_adapter",
    # Registry
    "ADAPTER_REGISTRY",
    "list_available_adapter_types",
    "list_available_adapter_subtypes",
    "get_adapter_info",
]


# Ensure dual registration in sys.modules for smooth resolution
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters"] = _mod
    sys.modules["optimization_core.adapters"] = _mod
