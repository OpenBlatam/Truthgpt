"""
Optimization Core Factories Package
===================================
Enterprise factory infrastructure for dynamic instantiation of model components, optimizers, datasets, loggers, and metrics.
"""

import logging
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Export Custom Exceptions
from .exceptions import (
    BuildError,
    DuplicateRegistrationError,
    FactoryConfigurationError,
    FactoryError,
    HardwareConstraintError,
    KeyNotFoundError,
    RegistryError,
    ScopeLifecycleError,
    TypeMismatchError,
    DependencyResolutionError,
)

# Export Base abstractions & Protocols
from .base import (
    BaseFactory,
    FactoryMetadata,
    FactoryScope,
    ManagedInstance,
    RegistryItem,
)

from .protocols import (
    BuilderProtocol,
    ConfigurableProtocol,
    ExtendedLifecycleProtocol,
    FactoryProtocol,
    HardwareAwareProtocol,
    LifecycleProtocol,
    RegistryProtocol,
    SerializableProtocol,
    TelemetryAwareProtocol,
    ValidatorProtocol,
)

from .utils import (
    detect_hardware_capabilities,
    filter_valid_kwargs,
    has_package,
    inspect_callable_args,
    safe_import,
    validate_callable_args,
)

# Import main Registry
from .registry import Registry

# Import Attention Factories
from .attention import (
    ATTENTION_BACKENDS,
    AttentionConfig,
    auto_select_attention_backend,
    build_flex,
    build_flash,
    build_math,
    build_ring,
    build_sage,
    build_sdpa,
    build_triton,
    build_xformers,
    get_available_attention_backends,
    math_attention,
    sdpa_attention,
)

# Import Optimizer Factories
from .optimizer import (
    OPTIMIZERS,
    SCHEDULERS,
    LRSchedulerConfig,
    OptimizerConfig,
    build_adafactor,
    build_adam,
    build_adamw,
    build_adamw_8bit,
    build_cosine,
    build_linear,
    build_lion,
    build_one_cycle,
    build_plateau,
    build_polynomial,
    build_rmsprop,
    build_scheduler,
    build_sgd,
    create_param_groups,
)

# Import Dataset Factories
from .datasets import (
    DATASETS,
    DatasetConfig,
    build_csv,
    build_hf,
    build_jsonl,
    build_parquet,
    build_synthetic,
    build_webdataset,
)

# Import Callback Factories
from .callbacks import (
    CALLBACKS,
    CallbackConfig,
    CSVLoggerCallback,
    CompositeCallback,
    CompositeLogger,
    CsvLogger,
    EarlyStoppingCallback,
    JSONLoggerCallback,
    JsonlLogger,
    PrintLogger,
    TensorBoardLogger,
    WandbLogger,
    build_composite,
    build_composite_callback,
    build_csv,
    build_early_stopping,
    build_jsonl as build_jsonl_logger,
    build_print,
    build_tensorboard,
    build_wandb,
)

# Import Collate Factories
from .collate import (
    COLLATE,
    COLLATE as COLLATORS,
    CollateConfig,
    build_cv_collate,
    build_lm_collate,
    build_masked_lm_collate,
    build_packed_lm_collate,
    build_seq_collate,
    build_vl_collate,
)

# Import KV Cache Factories
from .kv_cache import (
    KV_CACHE,
    KV_CACHE as KV_CACHE_FACTORIES,
    KVCacheConfig,
    KVCacheMemoryEstimate,
    PagedKVCache,
    SlidingWindowKVCache,
    StandardKVCache,
    build_chunked as build_chunked_kv_cache,
    build_none as build_kv_cache_none,
    build_paged as build_kv_cache_paged,
    build_quantized as build_quantized_kv_cache,
    build_sliding_window as build_sliding_window_kv_cache,
    build_standard as build_standard_kv_cache,
    estimate_kv_cache_memory,
)

# Import Memory Factories
from .memory import (
    MEMORY_MANAGERS,
    MEMORY_MANAGERS as MEMORY_FACTORIES,
    MemoryConfig,
    auto_memory_policy,
    build_adaptive as build_memory_adaptive,
    build_cpu_offload,
    build_cuda_ipc_pool,
    build_deepspeed_zero,
    build_static as build_memory_static,
)

# Import Metrics Factories
from .metrics import (
    METRICS,
    MetricAggregator,
    MetricConfig,
    metric_accuracy,
    metric_bpc,
    metric_composite,
    metric_flops,
    metric_gpu_memory,
    metric_latency_p99,
    metric_loss,
    metric_ppl,
    metric_throughput,
    metric_vram_utilization,
)


# Helper accessor functions
def get_attention_backend(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get an attention backend by name."""
    return ATTENTION_BACKENDS.build(name, *args, **kwargs)


def get_optimizer(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get an optimizer by name."""
    return OPTIMIZERS.build(name, *args, **kwargs)


def get_dataset(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a dataset by name."""
    return DATASETS.build(name, *args, **kwargs)


def get_callback(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a callback by name."""
    return CALLBACKS.build(name, *args, **kwargs)


def get_collator(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a collator by name."""
    return COLLATORS.build(name, *args, **kwargs)


def get_kv_cache(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a KV cache by name."""
    return KV_CACHE_FACTORIES.build(name, *args, **kwargs)


def get_memory(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a memory manager by name."""
    return MEMORY_FACTORIES.build(name, *args, **kwargs)


def get_metric(name: str, *args: Any, **kwargs: Any) -> Any:
    """Get a metric by name."""
    return METRICS.build(name, *args, **kwargs)


# Aliases for backward compatibility
build_optimizer = get_optimizer
build_dataset = get_dataset
build_callback = get_callback
build_collator = get_collator
build_kv_cache = get_kv_cache
build_memory = get_memory
build_metric = get_metric


# Global Registry Map
FACTORY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "optimizer": {
        "registry": OPTIMIZERS,
        "module": "factories.optimizer",
        "description": "Optimizer factory for creating training optimizers",
        "helper": get_optimizer,
    },
    "scheduler": {
        "registry": SCHEDULERS,
        "module": "factories.optimizer",
        "description": "Learning rate scheduler factory",
        "helper": build_scheduler,
    },
    "attention": {
        "registry": ATTENTION_BACKENDS,
        "module": "factories.attention",
        "description": "Attention backend factory",
        "helper": get_attention_backend,
    },
    "dataset": {
        "registry": DATASETS,
        "module": "factories.datasets",
        "description": "Dataset factory",
        "helper": get_dataset,
    },
    "callback": {
        "registry": CALLBACKS,
        "module": "factories.callbacks",
        "description": "Callback and logger factory",
        "helper": get_callback,
    },
    "collator": {
        "registry": COLLATORS,
        "module": "factories.collate",
        "description": "Collator factory",
        "helper": get_collator,
    },
    "kv_cache": {
        "registry": KV_CACHE_FACTORIES,
        "module": "factories.kv_cache",
        "description": "KV cache factory",
        "helper": get_kv_cache,
    },
    "memory": {
        "registry": MEMORY_FACTORIES,
        "module": "factories.memory",
        "description": "Memory manager factory",
        "helper": get_memory,
    },
    "metric": {
        "registry": METRICS,
        "module": "factories.metrics",
        "description": "Metric calculation factory",
        "helper": get_metric,
    },
}


def create_factory(
    factory_type: str = "optimizer",
    name: Optional[str] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Unified factory dispatcher function to construct any registered factory item.
    """
    factory_type_key = factory_type.lower().strip()
    if factory_type_key not in FACTORY_REGISTRY:
        available = ", ".join(FACTORY_REGISTRY.keys())
        raise ValueError(
            f"Unknown factory type: '{factory_type}'. Available types: {available}"
        )

    if name is None:
        raise ValueError(
            f"Name parameter is required for factory type '{factory_type}'"
        )

    registry = FACTORY_REGISTRY[factory_type_key]["registry"]
    return registry.build(name, *args, **kwargs)


def list_available_factories() -> List[str]:
    """List all registered factory category identifiers."""
    return list(FACTORY_REGISTRY.keys())


def list_factory_items(factory_type: str) -> List[str]:
    """List all available item keys in a specific factory type."""
    factory_key = factory_type.lower().strip()
    if factory_key not in FACTORY_REGISTRY:
        raise ValueError(f"Unknown factory type: {factory_type}")
    registry = FACTORY_REGISTRY[factory_key]["registry"]
    return list(registry.keys())


def get_factory_info(factory_type: str) -> Dict[str, Any]:
    """Get rich details and item counts for a specific factory type."""
    factory_key = factory_type.lower().strip()
    if factory_key not in FACTORY_REGISTRY:
        raise ValueError(f"Unknown factory type: {factory_type}")

    entry = FACTORY_REGISTRY[factory_key]
    registry = entry["registry"]

    return {
        "type": factory_key,
        "module": entry["module"],
        "description": entry["description"],
        "available_items": list(registry.keys()),
        "item_count": len(registry),
    }


def inspect_registry_tree() -> Dict[str, List[str]]:
    """Produce a dictionary overview of all registries and their registered keys."""
    return {k: list_factory_items(k) for k in FACTORY_REGISTRY.keys()}


def print_factory_status() -> None:
    """Print clean summary report of all registered factories to stdout."""
    print("=" * 60)
    print("      OPTIMIZATION CORE FACTORY SYSTEM STATUS REPORT")
    print("=" * 60)
    for ftype in list_available_factories():
        info = get_factory_info(ftype)
        print(f" * Factory: [{ftype.upper()}] ({info['description']})")
        print(f"   Items ({info['item_count']}): {', '.join(info['available_items'])}")
    print("-" * 60)
    att_status = get_available_attention_backends()
    print(f" Hardware Attention Support: {att_status}")
    print("=" * 60)


def validate_all_factories() -> Dict[str, bool]:
    """Run sanity checks on all factories to ensure registries are populated."""
    results = {}
    for factory_type, entry in FACTORY_REGISTRY.items():
        reg = entry["registry"]
        results[factory_type] = len(reg) > 0
    return results


def auto_discover_plugins(
    package_or_path: str = "optimization_core.factories.plugins",
) -> int:
    """Dynamically scan and discover plugin factory modules."""
    mod = safe_import(package_or_path)
    if mod is None:
        return 0
    return 1


class MasterFactory:
    """
    Master Orchestrator for managing all optimization core registries and instantiating
    complete component pipelines from configuration dictionaries.
    """

    def __init__(self) -> None:
        self.registries: Dict[str, Registry] = {
            ft: entry["registry"] for ft, entry in FACTORY_REGISTRY.items()
        }

    def register_custom_factory(
        self, type_name: str, registry: Registry, description: str = ""
    ) -> None:
        """Register a custom user-defined factory sub-registry."""
        key = type_name.lower().strip()
        self.registries[key] = registry
        FACTORY_REGISTRY[key] = {
            "registry": registry,
            "module": getattr(registry, "__module__", "custom"),
            "description": description or f"Custom {type_name} factory",
            "helper": lambda name, *a, **kw: registry.build(name, *a, **kw),
        }

    def build_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build full component dictionary from structured configuration mapping.
        """
        built_components = {}
        for component_key, comp_cfg in config.items():
            if not isinstance(comp_cfg, dict):
                continue
            factory_type = comp_cfg.get(
                "type",
                comp_cfg.get(
                    "backend",
                    comp_cfg.get(
                        "name",
                        comp_cfg.get("policy", comp_cfg.get("strategy")),
                    ),
                ),
            )
            if component_key in FACTORY_REGISTRY:
                registry = FACTORY_REGISTRY[component_key]["registry"]
                kwargs = {
                    k: v
                    for k, v in comp_cfg.items()
                    if k not in ("type", "backend", "name", "policy", "strategy")
                }
                if factory_type:
                    built_components[component_key] = registry.build(
                        factory_type, **kwargs
                    )
        return built_components


# System module alias mapping at end of initialization
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["factories"] = _mod
    sys.modules["optimization_core.factories"] = _mod


__all__ = [
    "MasterFactory",
    # Custom Exceptions
    "FactoryError",
    "RegistryError",
    "KeyNotFoundError",
    "DuplicateRegistrationError",
    "TypeMismatchError",
    "BuildError",
    "FactoryConfigurationError",
    "HardwareConstraintError",
    "DependencyResolutionError",
    "ScopeLifecycleError",
    # Base abstractions
    "FactoryScope",
    "FactoryMetadata",
    "RegistryItem",
    "ManagedInstance",
    "BaseFactory",
    # Protocols
    "BuilderProtocol",
    "ConfigurableProtocol",
    "LifecycleProtocol",
    "ExtendedLifecycleProtocol",
    "FactoryProtocol",
    "RegistryProtocol",
    "ValidatorProtocol",
    "SerializableProtocol",
    "HardwareAwareProtocol",
    "TelemetryAwareProtocol",
    # Utilities
    "safe_import",
    "has_package",
    "inspect_callable_args",
    "validate_callable_args",
    "filter_valid_kwargs",
    "detect_hardware_capabilities",
    # Registries
    "Registry",
    "ATTENTION_BACKENDS",
    "OPTIMIZERS",
    "SCHEDULERS",
    "DATASETS",
    "CALLBACKS",
    "COLLATE",
    "COLLATORS",
    "KV_CACHE",
    "KV_CACHE_FACTORIES",
    "MEMORY_MANAGERS",
    "MEMORY_FACTORIES",
    "METRICS",
    # Configs
    "AttentionConfig",
    "OptimizerConfig",
    "LRSchedulerConfig",
    "DatasetConfig",
    "CallbackConfig",
    "CollateConfig",
    "KVCacheConfig",
    "MemoryConfig",
    "MetricConfig",
    # Dispatchers and Helpers
    "get_attention_backend",
    "get_optimizer",
    "get_dataset",
    "get_callback",
    "get_collator",
    "get_kv_cache",
    "get_memory",
    "get_metric",
    "create_factory",
    "list_available_factories",
    "list_factory_items",
    "get_factory_info",
    "inspect_registry_tree",
    "print_factory_status",
    "validate_all_factories",
    "auto_discover_plugins",
    "build_optimizer",
    "build_dataset",
    "build_callback",
    "build_collator",
    "build_kv_cache",
    "build_memory",
    "build_metric",
    # Subsystem builders
    "sdpa_attention",
    "math_attention",
    "build_sdpa",
    "build_math",
    "build_flash",
    "build_triton",
    "build_xformers",
    "build_sage",
    "build_ring",
    "build_flex",
    "auto_select_attention_backend",
    "get_available_attention_backends",
    "create_param_groups",
    "build_adamw",
    "build_adamw_8bit",
    "build_adam",
    "build_sgd",
    "build_rmsprop",
    "build_lion",
    "build_adafactor",
    "build_cosine",
    "build_linear",
    "build_polynomial",
    "build_one_cycle",
    "build_plateau",
    "build_scheduler",
    "build_hf",
    "build_jsonl",
    "build_webdataset",
    "build_parquet",
    "build_csv",
    "build_synthetic",
    "PrintLogger",
    "WandbLogger",
    "TensorBoardLogger",
    "CSVLoggerCallback",
    "JSONLoggerCallback",
    "EarlyStoppingCallback",
    "CsvLogger",
    "JsonlLogger",
    "CompositeLogger",
    "CompositeCallback",
    "build_print",
    "build_wandb",
    "build_tensorboard",
    "build_csv",
    "build_jsonl_logger",
    "build_early_stopping",
    "build_composite",
    "build_composite_callback",
    "build_lm_collate",
    "build_cv_collate",
    "build_seq_collate",
    "build_packed_lm_collate",
    "build_masked_lm_collate",
    "build_vl_collate",
    "StandardKVCache",
    "PagedKVCache",
    "SlidingWindowKVCache",
    "KVCacheMemoryEstimate",
    "build_kv_cache_none",
    "build_kv_cache_paged",
    "build_standard_kv_cache",
    "build_sliding_window_kv_cache",
    "build_chunked_kv_cache",
    "build_quantized_kv_cache",
    "estimate_kv_cache_memory",
    "build_memory_adaptive",
    "build_memory_static",
    "build_deepspeed_zero",
    "build_cpu_offload",
    "build_cuda_ipc_pool",
    "auto_memory_policy",
    "MetricAggregator",
    "metric_loss",
    "metric_ppl",
    "metric_accuracy",
    "metric_bpc",
    "metric_latency_p99",
    "metric_throughput",
    "metric_flops",
    "metric_vram_utilization",
    "metric_gpu_memory",
    "metric_composite",
]
