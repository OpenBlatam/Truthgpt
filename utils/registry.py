"""
Centralized Discovery and Factory Registry for Optimization Core Utilities.
===========================================================================
"""

from __future__ import annotations

import functools
import importlib
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

try:
    from .exceptions import RegistryError, UtilityNotFoundError
except (ImportError, ValueError):
    try:
        from exceptions import RegistryError, UtilityNotFoundError
    except (ImportError, ValueError):
        from utils.exceptions import RegistryError, UtilityNotFoundError



logger = logging.getLogger(__name__)


class UtilityRegistry:
    """Thread-safe registry for discovery, configuration, and instantiation of utilities."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._lazy_registry: Dict[str, Tuple[str, str, Dict[str, Any]]] = {}

    def register(
        self,
        name: str,
        factory: Optional[Union[Type[Any], Callable[..., Any]]] = None,
        category: str = "general",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        override: bool = False,
        aliases: Optional[List[str]] = None,
    ) -> Any:
        """Register a utility class, function, or factory into the registry."""
        def decorator(comp: Union[Type[Any], Callable[..., Any]]) -> Union[Type[Any], Callable[..., Any]]:
            name_key = name.strip().lower()
            with self._lock:
                if name_key in self._registry and not override:
                    raise RegistryError(
                        f"Utility '{name}' is already registered in category '{self._registry[name_key]['category']}'."
                    )
                self._registry[name_key] = {
                    "name": name,
                    "factory": comp,
                    "category": category,
                    "description": description,
                    "metadata": metadata or {},
                    "aliases": aliases or [],
                }
                if aliases:
                    for alias in aliases:
                        alias_key = alias.strip().lower()
                        self._registry[alias_key] = self._registry[name_key]

                logger.debug(f"Registered utility '{name}' under category '{category}'")
            return comp

        if factory is not None:
            return decorator(factory)
        return decorator

    def register_lazy(
        self,
        name: str,
        module_path: str,
        attribute_name: str,
        category: str = "general",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Register a lazy-loaded utility component."""
        name_key = name.strip().lower()
        with self._lock:
            info = {
                "name": name,
                "category": category,
                "description": description,
                "metadata": metadata or {},
                "aliases": aliases or [],
            }
            self._lazy_registry[name_key] = (module_path, attribute_name, info)
            if aliases:
                for alias in aliases:
                    alias_key = alias.strip().lower()
                    self._lazy_registry[alias_key] = self._lazy_registry[name_key]

    def _load_lazy_if_needed(self, name_key: str) -> None:
        """Load a lazy component if registered."""
        if name_key in self._lazy_registry and name_key not in self._registry:
            module_path, attr_name, info = self._lazy_registry[name_key]
            try:
                module = importlib.import_module(module_path)
                comp = getattr(module, attr_name)
                self._registry[name_key] = {
                    "name": info["name"],
                    "factory": comp,
                    "category": info["category"],
                    "description": info["description"],
                    "metadata": info["metadata"],
                    "aliases": info.get("aliases", []),
                }
            except Exception as e:
                logger.warning(f"Failed to lazy load utility '{name_key}' from {module_path}.{attr_name}: {e}")

    def is_registered(self, name: str) -> bool:
        """Check if a utility is registered."""
        name_key = name.strip().lower()
        with self._lock:
            return name_key in self._registry or name_key in self._lazy_registry

    def unregister(self, name: str) -> bool:
        """Unregister a utility by name."""
        name_key = name.strip().lower()
        with self._lock:
            found = False
            if name_key in self._registry:
                del self._registry[name_key]
                found = True
            if name_key in self._lazy_registry:
                del self._lazy_registry[name_key]
                found = True
            return found

    def get(self, name: str) -> Dict[str, Any]:
        """Retrieve registration entry for a utility."""
        name_key = name.strip().lower()
        with self._lock:
            self._load_lazy_if_needed(name_key)
            if name_key not in self._registry:
                available = self.list_all()
                raise UtilityNotFoundError(f"Utility '{name}' not found. Registered utilities: {available}")
            return self._registry[name_key]

    def get_class(self, name: str) -> Type[Any] | Callable[..., Any]:
        """Retrieve class or callable of a registered utility."""
        entry = self.get(name)
        return entry["factory"]

    def create(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate a registered utility component."""
        entry = self.get(name)
        factory = entry["factory"]
        try:
            return factory(*args, **kwargs)
        except Exception as e:
            raise RegistryError(f"Failed to instantiate utility '{name}' with factory {factory}: {e}") from e

    def list_all(self, category: Optional[str] = None) -> List[str]:
        """List names of all registered utilities, optionally filtered by category."""
        with self._lock:
            all_entries: Dict[str, str] = {}
            for k, e in self._registry.items():
                if category is None or e["category"].strip().lower() == category.strip().lower():
                    all_entries[e["name"]] = e["name"]

            for k, (mod, attr, info) in self._lazy_registry.items():
                if category is None or info["category"].strip().lower() == category.strip().lower():
                    all_entries[info["name"]] = info["name"]

            return sorted(list(all_entries.values()))

    def list_categories(self) -> List[str]:
        """List all distinct registered utility categories."""
        with self._lock:
            cats = set(e["category"] for e in self._registry.values())
            cats.update(info["category"] for _, _, info in self._lazy_registry.values())
            return sorted(list(cats))

    def get_info(self, name: str) -> Dict[str, Any]:
        """Get public metadata info about a registered utility."""
        name_key = name.strip().lower()
        with self._lock:
            self._load_lazy_if_needed(name_key)
            if name_key in self._registry:
                entry = self._registry[name_key]
                return {
                    "name": entry["name"],
                    "category": entry["category"],
                    "description": entry["description"],
                    "metadata": entry["metadata"],
                    "factory_name": getattr(entry["factory"], "__name__", str(entry["factory"])),
                    "is_lazy": False,
                }
            if name_key in self._lazy_registry:
                _, _, info = self._lazy_registry[name_key]
                return {
                    "name": info["name"],
                    "category": info["category"],
                    "description": info["description"],
                    "metadata": info["metadata"],
                    "factory_name": "lazy",
                    "is_lazy": True,
                }
            raise UtilityNotFoundError(f"Utility '{name}' not found.")

    def has(self, name: str) -> bool:
        """Check if a utility is registered."""
        name_key = name.strip().lower()
        with self._lock:
            return name_key in self._registry or name_key in self._lazy_registry

    def is_registered(self, name: str) -> bool:
        """Alias for has()."""
        return self.has(name)

    def is_available(self, name: str) -> bool:
        """Alias for has()."""
        return self.has(name)

    def clear(self) -> None:
        """Clear all registered utilities."""
        with self._lock:
            self._registry.clear()
            self._lazy_registry.clear()


# Global Singleton Registry Instance
UTILITY_REGISTRY = UtilityRegistry()


def register_utility(
    name: str,
    component: Optional[Type[Any] | Callable[..., Any]] = None,
    category: str = "general",
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    override: bool = False,
    aliases: Optional[List[str]] = None,
) -> Any:
    """Decorator or direct function to register a utility in the global registry."""
    return UTILITY_REGISTRY.register(
        name=name,
        factory=component,
        category=category,
        description=description,
        metadata=metadata,
        override=override,
        aliases=aliases,
    )


def create_utility(name: str, *args: Any, **kwargs: Any) -> Any:
    """Factory helper to instantiate any registered utility by name."""
    return UTILITY_REGISTRY.create(name, *args, **kwargs)


def list_available_utilities(category: Optional[str] = None) -> List[str]:
    """List all registered utilities."""
    return UTILITY_REGISTRY.list_all(category=category)


def get_utility_info(name: str) -> Dict[str, Any]:
    """Get metadata information about a registered utility."""
    return UTILITY_REGISTRY.get_info(name)


def get_utility_class(name: str) -> Type[Any] | Callable[..., Any]:
    """Retrieve the class or callable of a globally registered utility."""
    return UTILITY_REGISTRY.get_class(name)


def is_utility_available(name: str) -> bool:
    """Check if a utility is registered globally."""
    return UTILITY_REGISTRY.has(name)


# Pre-register built-in core utilities
def _init_default_registry() -> None:
    """Register built-in utility components across optimization_core."""
    # Base utilities
    UTILITY_REGISTRY.register_lazy("BaseOptimizationModel", "optimization_core.utils.base", "BaseOptimizationModel", "general", "Base Pydantic schema model")
    UTILITY_REGISTRY.register_lazy("CudaResourceManager", "optimization_core.utils.base", "CudaResourceManager", "hardware", "CUDA stream and device manager")

    # Logging
    UTILITY_REGISTRY.register_lazy("TrainingLogger", "optimization_core.utils.logging.basic", "TrainingLogger", "logging", "Structured training progress logger")
    UTILITY_REGISTRY.register_lazy("setup_logger", "optimization_core.utils.logging.basic", "setup_logger", "logging", "Configures structured stream/file loggers")

    # Training tools
    UTILITY_REGISTRY.register_lazy("visualize_checkpoints", "optimization_core.utils.visualize_training", "visualize_checkpoints", "training_tool", "Checkpoint visualizer and disk reporter")
    UTILITY_REGISTRY.register_lazy("summarize_run", "optimization_core.utils.visualize_training", "summarize_run", "training_tool", "Summary report for training run")
    UTILITY_REGISTRY.register_lazy("compare_runs", "optimization_core.utils.compare_runs", "compare_runs", "training_tool", "Run comparator across experiment metrics")
    UTILITY_REGISTRY.register_lazy("cleanup_runs", "optimization_core.utils.cleanup_runs", "cleanup_runs", "training_tool", "Disk space cleanup utility for checkpoints")

    # TruthGPT Core
    UTILITY_REGISTRY.register_lazy("TruthGPTConfig", "optimization_core.utils.truthgpt.core", "TruthGPTConfig", "truthgpt", "TruthGPT optimization configuration")
    UTILITY_REGISTRY.register_lazy("create_truthgpt_optimizer", "optimization_core.utils.truthgpt.core", "create_truthgpt_optimizer", "truthgpt", "Factory for TruthGPT integrated optimizers")

    # Resilience
    UTILITY_REGISTRY.register_lazy("CircuitBreaker", "optimization_core.utils.circuit_breaker", "CircuitBreaker", "resilience", "Circuit breaker fault-tolerance handler")
    UTILITY_REGISTRY.register_lazy("TaskScheduler", "optimization_core.utils.task_scheduler", "TaskScheduler", "concurrency", "Threaded background task scheduler")

    # Hardware / Memory
    UTILITY_REGISTRY.register_lazy("MemoryOptimizer", "optimization_core.utils.memory.optimizations", "MemoryOptimizer", "memory", "Dynamic activation and memory optimizer")
    UTILITY_REGISTRY.register_lazy("TensorPool", "optimization_core.utils.memory.pooling", "TensorPool", "memory", "Pre-allocated tensor memory pool")
    UTILITY_REGISTRY.register_lazy("CUDAOptimizations", "optimization_core.utils.gpu.cuda_kernels", "CUDAOptimizations", "hardware", "Custom CUDA fused kernels and LayerNorm")

    # Optimizers
    UTILITY_REGISTRY.register_lazy("HyperSpeedOptimizer", "optimization_core.utils.hyper_speed_optimizer", "HyperSpeedOptimizer", "optimizer", "High-throughput kernel optimizer")
    UTILITY_REGISTRY.register_lazy("AutoPerformanceOptimizer", "optimization_core.utils.auto_performance_optimizer", "AutoPerformanceOptimizer", "optimizer", "Dynamic hardware performance auto-tuner")
    UTILITY_REGISTRY.register_lazy("NeuralEvolutionaryOptimizer", "optimization_core.utils.neural_evolutionary_optimizer", "NeuralEvolutionaryOptimizer", "optimizer", "Evolutionary architecture optimizer")


_init_default_registry()


__all__ = [
    "UtilityRegistry",
    "UTILITY_REGISTRY",
    "register_utility",
    "create_utility",
    "list_available_utilities",
    "get_utility_info",
    "get_utility_class",
    "is_utility_available",
]
