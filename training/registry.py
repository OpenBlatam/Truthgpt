"""
Training Component Registry and Factory System
==============================================
Thread-safe registry for training loops, checkpoint managers, EMA managers,
evaluators, experiment trackers, callbacks, and pipelines.
Provides decorator-based registration, discovery APIs, and unified factory instantiation.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import TrainingConfigurationError, TrainingError
from .types import TrainingComponentInfo

logger = logging.getLogger(__name__)

DEFAULT_TRAINING_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "training_loop": {
        "class": "TrainingLoop",
        "module": ".training_loop",
        "description": "Modular training loop with AMP, gradient accumulation, and clipping",
        "aliases": ["loop", "trainer_loop", "training-loop"],
    },
    "checkpoint_manager": {
        "class": "CheckpointManager",
        "module": ".checkpoint_manager",
        "description": "Atomic model checkpointing with RNG preservation and automated pruning",
        "aliases": ["checkpoint", "checkpointing", "checkpoints", "checkpoint-manager"],
    },
    "ema_manager": {
        "class": "EMAManager",
        "module": ".ema_manager",
        "description": "Exponential Moving Average parameter tracking with CPU offloading and weight swapping",
        "aliases": ["ema", "ema_tracker", "ema-manager"],
    },
    "evaluator": {
        "class": "Evaluator",
        "module": ".evaluator",
        "description": "Evaluation engine supporting AMP, custom metrics, and perplexity calculation",
        "aliases": ["evaluation", "eval", "model_evaluator"],
    },
    "experiment_tracker": {
        "class": "ExperimentTracker",
        "module": ".experiment_tracker",
        "description": "Multi-backend experiment tracker (WandB, TensorBoard, MLflow, Console)",
        "aliases": ["tracker", "tracking", "logger_tracker", "experiment-tracker"],
    },
    "training_pipeline": {
        "class": "TrainingPipeline",
        "module": ".pipeline",
        "description": "End-to-end training pipeline orchestrator with full lifecycle management",
        "aliases": ["pipeline", "orchestrator", "training-pipeline"],
    },
    "pipeline_builder": {
        "class": "TrainingPipelineBuilder",
        "module": ".pipeline",
        "description": "Fluent builder for configuring and assembling TrainingPipeline instances",
        "aliases": ["builder", "training_builder", "pipeline-builder"],
    },
}


class TrainingRegistry:
    """
    Thread-safe registry for training classes and factory functions with lazy loading.
    """

    _instance: Optional["TrainingRegistry"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> "TrainingRegistry":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(TrainingRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._alias_map: Dict[str, str] = {}
        self._lock = threading.RLock()
        self._init_defaults()
        self._initialized = True

    def _init_defaults(self) -> None:
        for name, meta in DEFAULT_TRAINING_DEFINITIONS.items():
            canon = name.lower().replace("-", "_")
            self._registry[canon] = {
                "name": canon,
                "class_or_factory": None,
                "class": meta["class"],
                "description": meta["description"],
                "module": meta["module"],
                "aliases": [a.lower().replace("-", "_") for a in meta.get("aliases", [])],
            }
            for alias in meta.get("aliases", []):
                self._alias_map[alias.lower().replace("-", "_")] = canon

    def register(
        self,
        name: str,
        class_or_factory: Union[Type[Any], Callable[..., Any]],
        description: str = "",
        aliases: Optional[List[str]] = None,
        override: bool = False,
    ) -> None:
        """
        Register a new training component class or factory function.
        """
        with self._lock:
            canon = name.lower().replace("-", "_")
            if canon in self._registry and not override:
                logger.debug(f"Training component '{canon}' already registered; skipping without override.")
                return

            alias_list = [a.lower().replace("-", "_") for a in (aliases or [])]
            self._registry[canon] = {
                "name": canon,
                "class_or_factory": class_or_factory,
                "class": class_or_factory.__name__ if hasattr(class_or_factory, "__name__") else str(class_or_factory),
                "description": description or getattr(class_or_factory, "__doc__", "") or "",
                "module": getattr(class_or_factory, "__module__", ""),
                "aliases": alias_list,
            }
            for a in alias_list:
                self._alias_map[a] = canon
            logger.debug(f"Registered training component '{canon}' with aliases {alias_list}.")

    def _resolve_name(self, name: str) -> str:
        k = name.lower().replace("-", "_")
        return self._alias_map.get(k, k)

    def get(self, name: str) -> Type[Any]:
        """
        Resolve and load the component class or factory.
        """
        with self._lock:
            canon = self._resolve_name(name)
            if canon not in self._registry:
                avail = ", ".join(sorted(self._registry.keys()))
                raise TrainingConfigurationError(
                    f"Unknown training component '{name}'. Available: [{avail}]"
                )

            entry = self._registry[canon]
            if entry["class_or_factory"] is not None:
                return entry["class_or_factory"]

            # Lazy-import class matching active package
            module_name = entry["module"]
            class_name = entry["class"]
            pkg = __package__ or "training"
            try:
                if module_name.startswith("."):
                    mod = importlib.import_module(module_name, package=pkg)
                else:
                    mod = importlib.import_module(module_name)
                cls_obj = getattr(mod, class_name)
                entry["class_or_factory"] = cls_obj
                return cls_obj
            except Exception as e:
                raise TrainingConfigurationError(
                    f"Failed to load training component '{name}' ({module_name}.{class_name}): {e}"
                ) from e

    def get_info(self, name: str) -> Optional[TrainingComponentInfo]:
        """Get structured metadata for a registered component."""
        with self._lock:
            canon = self._resolve_name(name)
            if canon not in self._registry:
                return None
            e = self._registry[canon]
            return TrainingComponentInfo(
                name=e["name"],
                component_type="training",
                class_name=e["class"],
                module=e["module"],
                description=e["description"],
                aliases=list(e.get("aliases", [])),
            )

    def list_components(self) -> List[str]:
        """Return sorted list of all primary registered component names."""
        with self._lock:
            return sorted(list(self._registry.keys()))

    def create(
        self,
        component_type: str,
        config: Optional[Union[Dict[str, Any], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Instantiate a training component dynamically.
        """
        cls_obj = self.get(component_type)
        params: Dict[str, Any] = {}

        if config is not None:
            if hasattr(config, "__dict__") and not isinstance(config, dict):
                params.update(vars(config))
            elif isinstance(config, dict):
                params.update(config)

        params.update(kwargs)

        try:
            sig = inspect.signature(cls_obj.__init__)
            accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

            if accepts_kwargs:
                return cls_obj(**params)

            # Filter valid constructor args
            valid_keys = set(sig.parameters.keys()) - {"self"}
            filtered = {k: v for k, v in params.items() if k in valid_keys}
            return cls_obj(**filtered)
        except Exception as e:
            if isinstance(e, (TrainingError, TrainingConfigurationError)):
                raise
            raise TrainingError(f"Failed to instantiate training component '{component_type}': {e}") from e


# Global registry singleton instance
TRAINING_REGISTRY = TrainingRegistry()


def register_training_component(
    name: str,
    aliases: Optional[List[str]] = None,
    description: str = "",
    override: bool = False,
) -> Callable[[Type[Any]], Type[Any]]:
    """
    Decorator for registering training components into TRAINING_REGISTRY.
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        TRAINING_REGISTRY.register(
            name=name,
            class_or_factory=cls,
            description=description,
            aliases=aliases,
            override=override,
        )
        return cls
    return decorator


def create_training_component(
    component_type: str = "training_loop",
    config: Optional[Union[Dict[str, Any], Any]] = None,
    **kwargs: Any,
) -> Any:
    """Unified factory entry point for creating any training component."""
    return TRAINING_REGISTRY.create(component_type=component_type, config=config, **kwargs)


def list_available_training_components() -> List[str]:
    """Return all available training component identifiers."""
    return TRAINING_REGISTRY.list_components()


def get_training_component_info(name: str) -> Optional[Dict[str, Any]]:
    """Return metadata dictionary for a specific training component."""
    info = TRAINING_REGISTRY.get_info(name)
    if info is None:
        return None
    return {
        "name": info.name,
        "class": info.class_name,
        "module": info.module,
        "description": info.description,
        "aliases": info.aliases,
    }
