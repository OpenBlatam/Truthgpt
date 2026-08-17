"""
Data loading and processing modules.

This module provides organized access to data components:
- Dataset management
- Data loader factories
- Data collators
- Data processor factory & Polars processor
- Dataset builder registry
- Text processing
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

# Direct imports for backward compatibility
from .dataset_manager import DatasetManager
from .data_loader_factory import DataLoaderFactory, DataLoaderBuilder, LengthBucketBatchSampler, LengthBucketSampler
from .collators import BaseCollator, LMCollator, ClassificationCollator
from .base_processor import BaseDataProcessor
from .processor_factory import (
    create_data_processor,
    ProcessorType,
    PandasProcessor,
    list_available_processors,
    get_processor_recommendation,
    get_processor_info,
)
from .polars_processor import PolarsProcessor, create_polars_processor
from .registry import (
    DatasetRegistry,
    default_registry,
    register_dataset,
    unregister_dataset,
    build_dataset,
    has_dataset,
    get_dataset_info,
    list_registered_datasets,
    get_dataset_builder,
    clear_dataset_registry,
)

logger = logging.getLogger(__name__)

# Lazy imports for additional components
_LAZY_IMPORTS = {
    'text_hf': 'optimization_core.data.text_hf',
    'registry': 'optimization_core.data.registry',
    'processor_factory': 'optimization_core.data.processor_factory',
    'polars_processor': 'optimization_core.data.polars_processor',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for data submodules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    import importlib
    try:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        _import_cache[name] = module
        return module
    except Exception as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def create_data_component(component_type: str = "dataset_manager", config: Optional[dict] = None) -> Any:
    """
    Unified factory function to create data components.
    
    Args:
        component_type: Type of component. Options: 
            "dataset_manager", "data_loader_factory", "data_loader_builder",
            "length_bucket_batch_sampler", "collator", "processor_factory", "polars_processor"
        config: Optional configuration dictionary
    
    Returns:
        The requested component instance or function
    """
    if config is None:
        config = {}
    
    component_type = component_type.lower()
    
    factory_map = {
        "dataset_manager": lambda cfg: DatasetManager(cfg),
        "data_loader_factory": lambda cfg: DataLoaderFactory(),
        "data_loader_builder": lambda cfg: DataLoaderBuilder(),
        "length_bucket_batch_sampler": lambda cfg: LengthBucketBatchSampler(**cfg),
        "collator": lambda cfg: LMCollator(**cfg),
        "classification_collator": lambda cfg: ClassificationCollator(**cfg),
        "processor_factory": lambda cfg: create_data_processor(**cfg),
        "polars_processor": lambda cfg: PolarsProcessor(**cfg),
        "pandas_processor": lambda cfg: PandasProcessor(**cfg),
        "create_polars_processor": lambda cfg: create_polars_processor(**cfg),
        "dataset_registry": lambda cfg: DatasetRegistry(),
    }
    
    if component_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown data component type: '{component_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[component_type]
    return factory(config)


DATA_COMPONENT_REGISTRY = {
    "dataset_manager": {
        "class": DatasetManager,
        "module": "data.dataset_manager",
    },
    "data_loader_factory": {
        "class": DataLoaderFactory,
        "module": "data.data_loader_factory",
    },
    "data_loader_builder": {
        "class": DataLoaderBuilder,
        "module": "data.data_loader_factory",
    },
    "length_bucket_batch_sampler": {
        "class": LengthBucketBatchSampler,
        "module": "data.data_loader_factory",
    },
    "collator": {
        "class": LMCollator,
        "module": "data.collators",
    },
    "classification_collator": {
        "class": ClassificationCollator,
        "module": "data.collators",
    },
    "processor_factory": {
        "function": create_data_processor,
        "module": "data.processor_factory",
    },
    "polars_processor": {
        "class": PolarsProcessor,
        "module": "data.polars_processor",
    },
    "pandas_processor": {
        "class": PandasProcessor,
        "module": "data.processor_factory",
    },
    "registry": {
        "function": build_dataset,
        "module": "data.registry",
    },
    "dataset_registry": {
        "class": DatasetRegistry,
        "module": "data.registry",
    },
}


def list_available_data_components() -> List[str]:
    """List all available data component types."""
    return list(DATA_COMPONENT_REGISTRY.keys())


def get_data_component_info(component_type: str) -> Dict[str, Any]:
    """Get information about a data component."""
    if component_type not in DATA_COMPONENT_REGISTRY:
        raise ValueError(f"Unknown data component: {component_type}")
    
    entry = DATA_COMPONENT_REGISTRY[component_type]
    target = entry.get("class") or entry.get("function")
    target_name = target.__name__ if target else component_type
    
    return {
        'name': component_type,
        'target': target_name,
        'module': entry['module'],
    }


__all__ = [
    "DatasetManager",
    "DataLoaderFactory",
    "DataLoaderBuilder",
    "LengthBucketBatchSampler",
    "LengthBucketSampler",
    "BaseCollator",
    "LMCollator",
    "ClassificationCollator",
    "BaseDataProcessor",
    "PolarsProcessor",
    "PandasProcessor",
    "ProcessorType",
    "create_data_processor",
    "create_polars_processor",
    "list_available_processors",
    "get_processor_recommendation",
    "get_processor_info",
    "DatasetRegistry",
    "default_registry",
    "register_dataset",
    "unregister_dataset",
    "build_dataset",
    "has_dataset",
    "get_dataset_info",
    "list_registered_datasets",
    "get_dataset_builder",
    "clear_dataset_registry",
    "create_data_component",
    "list_available_data_components",
    "get_data_component_info",
    "DATA_COMPONENT_REGISTRY",
]


