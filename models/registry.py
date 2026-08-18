"""
Model Registry and Factory System
==================================
Thread-safe registry for model implementations, pipelines, builders, and managers.
Provides decorator-based registration, discovery APIs, and unified factory dispatch.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import ModelConfigurationError, ModelNotFoundError
from .types import ModelInfo

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "manager": {
        "class": "ModelManager",
        "module": ".model_manager",
        "description": "Model manager for loading, saving, device placement, and hardware acceleration",
        "aliases": ["model_manager", "manager_core", "model-manager"],
    },
    "builder": {
        "class": "ModelBuilder",
        "module": ".model_builder",
        "description": "Fluent builder pattern for constructing configured PyTorch models",
        "aliases": ["model_builder", "model-builder"],
    },
    "diffusion": {
        "class": "DiffusionModelManager",
        "module": ".diffusion_manager",
        "description": "Diffusion model manager for Stable Diffusion and SDXL pipelines",
        "aliases": ["diffusion_manager", "diffusion_model_manager", "diffusion-manager"],
    },
    "hf_transformers": {
        "class": "HFTransformersModel",
        "module": ".hf_transformers",
        "description": "HuggingFace Transformers model wrapper with inference optimizations",
        "aliases": ["hf_llm", "transformers", "hf-transformers", "llm"],
    },
    "hf_diffusers": {
        "class": "HFDiffusersModel",
        "module": ".hf_diffusers",
        "description": "HuggingFace Diffusers integration for generative image pipelines",
        "aliases": ["hf_diffusion", "diffusers", "hf-diffusers", "diffusion_model_hf"],
    },
    "truthgpt": {
        "class": "TruthGPTModel",
        "module": ".models",
        "description": "Native TruthGPT high-performance autoregressive transformer architecture",
        "aliases": ["truthgpt_model", "truthgpt_transformer", "truthgpt_causal"],
    },
    "attention": {
        "class": "EfficientAttention",
        "module": ".attention_utils",
        "description": "Efficient Multi-Head Attention kernel module with Flash/SDPA/xFormers",
        "aliases": ["efficient_attention", "attention_module"],
    },
}


class ModelRegistry:
    """
    Thread-safe registry for model classes and factory functions with lazy loading.
    """

    _instance: Optional["ModelRegistry"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> "ModelRegistry":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(ModelRegistry, cls).__new__(cls)
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
        for name, meta in DEFAULT_MODEL_DEFINITIONS.items():
            canon = name.lower().replace("-", "_")
            self._registry[canon] = {
                "name": canon,
                "class_or_factory": None,
                "class": meta["class"],
                "description": meta["description"],
                "module": meta["module"],
                "aliases": [a.lower().replace("-", "_") for a in meta.get("aliases", [])],
            }
            self._alias_map[canon] = canon
            for alias in meta.get("aliases", []):
                self._alias_map[alias.lower().replace("-", "_")] = canon

    def register(
        self,
        name: str,
        cls_or_factory: Union[Type[Any], Callable[..., Any]],
        aliases: Optional[List[str]] = None,
        description: str = "",
        module_path: Optional[str] = None,
    ) -> None:
        """Register a model class or factory."""
        canon_name = name.lower().replace("-", "_")
        with self._lock:
            class_name = getattr(cls_or_factory, "__name__", str(cls_or_factory))
            clean_aliases = [a.lower().replace("-", "_") for a in (aliases or [])]
            self._registry[canon_name] = {
                "name": canon_name,
                "class_or_factory": cls_or_factory,
                "class": class_name,
                "description": description or getattr(cls_or_factory, "__doc__", "") or "Model component",
                "module": module_path or getattr(cls_or_factory, "__module__", ""),
                "aliases": clean_aliases,
            }
            self._alias_map[canon_name] = canon_name
            for alias in clean_aliases:
                self._alias_map[alias] = canon_name
            logger.debug(f"Registered model '{canon_name}'")

    def unregister(self, name: str) -> bool:
        """Unregister a model by name or alias."""
        with self._lock:
            canon = self.get_canonical_name(name)
            if canon in self._registry:
                entry = self._registry.pop(canon)
                self._alias_map.pop(canon, None)
                for alias in entry.get("aliases", []):
                    self._alias_map.pop(alias, None)
                return True
            return False

    def register_decorator(
        self,
        name: str,
        aliases: Optional[List[str]] = None,
        description: str = "",
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator for registering model classes."""
        def decorator(cls: Type[Any]) -> Type[Any]:
            self.register(name, cls, aliases=aliases, description=description)
            return cls
        return decorator

    def get_canonical_name(self, name: str) -> str:
        key = name.lower().replace("-", "_")
        return self._alias_map.get(key, key)

    def _resolve_lazy(self, canon_name: str) -> Any:
        entry = self._registry[canon_name]
        if entry["class_or_factory"] is not None:
            return entry["class_or_factory"]

        mod_name = entry["module"]
        if mod_name.startswith("."):
            mod = importlib.import_module(mod_name, __package__ or "optimization_core.models")
        else:
            mod = importlib.import_module(mod_name)

        cls_or_fact = getattr(mod, entry["class"])
        entry["class_or_factory"] = cls_or_fact
        return cls_or_fact

    def get(self, name: str) -> Any:
        """Retrieve the registered class or factory callable."""
        canon = self.get_canonical_name(name)
        with self._lock:
            if canon not in self._registry:
                available = self.list_available()
                raise ModelNotFoundError(
                    f"Unknown model type: '{name}'. Available models: {', '.join(available)}",
                    model_name=name,
                )
            return self._resolve_lazy(canon)

    def get_class(self, name: str) -> Type[Any]:
        """Retrieve registered class."""
        return self.get(name)

    def list_models(self) -> List[str]:
        """Return list of all registered canonical model names."""
        with self._lock:
            return sorted(list(self._registry.keys()))

    def list_available(self) -> List[str]:
        """Return list of all registered canonical model names."""
        return self.list_models()

    def list_all_aliases(self) -> List[str]:
        """Return list of all registered model names and aliases."""
        with self._lock:
            return sorted(list(self._alias_map.keys()))

    def get_info(self, name: str) -> ModelInfo:
        """Get ModelInfo metadata for a model type."""
        canon = self.get_canonical_name(name)
        with self._lock:
            if canon not in self._registry:
                raise ModelNotFoundError(f"Unknown model type: '{name}'", model_name=name)
            entry = self._registry[canon]
            return ModelInfo(
                name=entry["name"],
                cls_name=entry["class"],
                module=entry["module"],
                description=entry["description"],
                aliases=entry.get("aliases", []),
                tags=[],
            )

    def create(
        self,
        model_type: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Instantiate a registered model with given configuration and arguments."""
        factory_or_cls = self.get(model_type)
        cfg = dict(config or {})
        cfg.update(kwargs)

        try:
            if callable(factory_or_cls):
                # Try calling with config dict first if accepted
                sig = inspect.signature(factory_or_cls) if hasattr(inspect, "signature") else None
                if sig is not None:
                    params = sig.parameters
                    if "config" in params and len(params) == 1 and not cfg:
                        return factory_or_cls(config=cfg)
                    if "config" in params and len(params) == 1:
                        return factory_or_cls(config=cfg)

                # Try keyword arguments
                try:
                    return factory_or_cls(**cfg)
                except TypeError:
                    # Fallback to single config dict argument
                    try:
                        return factory_or_cls(cfg)
                    except TypeError:
                        # Fallback to empty init
                        return factory_or_cls()

            raise ModelConfigurationError(
                f"Registered target '{model_type}' is not callable",
                model_name=model_type,
            )
        except Exception as e:
            if isinstance(e, (ModelNotFoundError, ModelConfigurationError)):
                raise
            logger.error(f"Failed to create model '{model_type}': {e}", exc_info=True)
            raise ModelConfigurationError(
                f"Error initializing model '{model_type}': {e}",
                model_name=model_type,
                original_exception=e,
            ) from e

    def __contains__(self, name: str) -> bool:
        return self.get_canonical_name(name) in self._registry


MODEL_REGISTRY = ModelRegistry()


def register_model(
    name: str,
    aliases: Optional[List[str]] = None,
    description: str = "",
) -> Callable[[Type[Any]], Type[Any]]:
    """Decorator to register a model class into the global MODEL_REGISTRY."""
    return MODEL_REGISTRY.register_decorator(name, aliases=aliases, description=description)


def register_model_class(
    name: str,
    cls: Type[Any],
    aliases: Optional[List[str]] = None,
    description: str = "",
) -> None:
    """Register a model class directly."""
    MODEL_REGISTRY.register(name, cls, aliases=aliases, description=description)


def get_registered_class(name: str) -> Optional[Type[Any]]:
    """Get registered class or None if not found."""
    try:
        return MODEL_REGISTRY.get(name)
    except Exception:
        return None


def get_model_class(name: str) -> Type[Any]:
    """Get registered model class or raise ModelNotFoundError."""
    return MODEL_REGISTRY.get(name)


def list_available_models() -> List[str]:
    """List all available model canonical names."""
    return MODEL_REGISTRY.list_available()


def get_model_info(model_type: str) -> Dict[str, Any]:
    """Get model metadata as a dictionary."""
    info = MODEL_REGISTRY.get_info(model_type)
    return {
        "type": info.name,
        "name": info.name,
        "class": info.cls_name,
        "module": info.module,
        "description": info.description,
        "aliases": info.aliases,
    }


def create_model(
    model_type: str = "manager",
    config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    """Unified factory to create any registered model, manager, or builder."""
    return MODEL_REGISTRY.create(model_type, config=config, **kwargs)


build_model = create_model


__all__ = [
    "ModelRegistry",
    "MODEL_REGISTRY",
    "DEFAULT_MODEL_DEFINITIONS",
    "register_model",
    "register_model_class",
    "get_registered_class",
    "get_model_class",
    "list_available_models",
    "get_model_info",
    "create_model",
    "build_model",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
