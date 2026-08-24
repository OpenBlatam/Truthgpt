"""
Component and Strategy Registry for Learning Subsystem
======================================================
Provides a thread-safe, extensible registry for dynamically discovering,
registering, and instantiating learners, optimizers, samplers, and pipeline stages.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import LearnerNotFoundError, StrategyNotSupportedError
from .types import LearningStrategyType

logger = logging.getLogger(__name__)


class LearningRegistry:
    """
    Thread-safe central registry for all learning components and algorithms.
    """

    _lock: threading.Lock = threading.Lock()
    _learners: Dict[str, Any] = {}
    _optimizers: Dict[str, Any] = {}
    _strategies: Dict[str, Any] = {}
    _samplers: Dict[str, Any] = {}
    _callbacks: Dict[str, Any] = {}
    _aliases: Dict[str, str] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: Union[str, LearningStrategyType],
        factory_or_cls: Any,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Any:
        """Register a learner or optimizer factory/class directly."""
        key = name.value if isinstance(name, LearningStrategyType) else str(name).lower()
        with cls._lock:
            cls._learners[key] = factory_or_cls
            cls._metadata[key] = {
                "name": key,
                "target": factory_or_cls,
                "description": description or f"Learning component {key}",
                **kwargs,
            }
            if aliases:
                for alias in aliases:
                    cls._aliases[alias.lower()] = key
        return factory_or_cls

    @classmethod
    def register_learner(
        cls,
        name: Union[str, LearningStrategyType],
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a learner class."""
        def decorator(target_cls: Type[Any]) -> Type[Any]:
            key = name.value if isinstance(name, LearningStrategyType) else str(name).lower()
            with cls._lock:
                cls._learners[key] = target_cls
                cls._metadata[key] = {
                    "name": key,
                    "target": target_cls,
                    "description": description or target_cls.__doc__ or f"Learner {key}",
                    **kwargs,
                }
                if aliases:
                    for alias in aliases:
                        cls._aliases[alias.lower()] = key
            logger.debug("Registered learner: '%s' -> %s", key, target_cls.__name__)
            return target_cls
        return decorator

    @classmethod
    def register_optimizer(
        cls,
        name: Union[str, LearningStrategyType],
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a learning search or optimization algorithm."""
        def decorator(target_cls: Type[Any]) -> Type[Any]:
            key = name.value if isinstance(name, LearningStrategyType) else str(name).lower()
            with cls._lock:
                cls._optimizers[key] = target_cls
                cls._metadata[key] = {
                    "name": key,
                    "target": target_cls,
                    "description": description or target_cls.__doc__ or f"Optimizer {key}",
                    **kwargs,
                }
                if aliases:
                    for alias in aliases:
                        cls._aliases[alias.lower()] = key
            logger.debug("Registered learning optimizer: '%s' -> %s", key, target_cls.__name__)
            return target_cls
        return decorator

    @classmethod
    def register_strategy(
        cls,
        name: str,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a specialized learning strategy."""
        def decorator(target_cls: Type[Any]) -> Type[Any]:
            key = str(name).lower()
            with cls._lock:
                cls._strategies[key] = target_cls
                cls._metadata[key] = {
                    "name": key,
                    "target": target_cls,
                    "description": description or target_cls.__doc__ or f"Strategy {key}",
                    **kwargs,
                }
                if aliases:
                    for alias in aliases:
                        cls._aliases[alias.lower()] = key
            logger.debug("Registered strategy: '%s' -> %s", key, target_cls.__name__)
            return target_cls
        return decorator

    @classmethod
    def register_sampler(
        cls,
        name: str,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a query sampler."""
        def decorator(target_cls: Type[Any]) -> Type[Any]:
            key = str(name).lower()
            with cls._lock:
                cls._samplers[key] = target_cls
                cls._metadata[key] = {
                    "name": key,
                    "target": target_cls,
                    "description": description or target_cls.__doc__ or f"Sampler {key}",
                    **kwargs,
                }
                if aliases:
                    for alias in aliases:
                        cls._aliases[alias.lower()] = key
            logger.debug("Registered sampler: '%s' -> %s", key, target_cls.__name__)
            return target_cls
        return decorator

    @classmethod
    def register_callback(
        cls,
        name: str,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a lifecycle callback."""
        def decorator(target_cls: Type[Any]) -> Type[Any]:
            key = str(name).lower()
            with cls._lock:
                cls._callbacks[key] = target_cls
                cls._metadata[key] = {
                    "name": key,
                    "target": target_cls,
                    "description": description or target_cls.__doc__ or f"Callback {key}",
                    **kwargs,
                }
                if aliases:
                    for alias in aliases:
                        cls._aliases[alias.lower()] = key
            logger.debug("Registered callback: '%s' -> %s", key, target_cls.__name__)
            return target_cls
        return decorator

    _BUILTIN_LEARNERS: Dict[str, tuple[str, str]] = {
        'active': ('.active_learning', 'ActiveLearningSystem'),
        'adaptive': ('.adaptive_learning', 'AdaptiveLearningSystem'),
        'adversarial': ('.adversarial_learning', 'AdversarialLearningSystem'),
        'bayesian': ('.bayesian_optimization', 'BayesianOptimizer'),
        'causal': ('.causal_inference', 'CausalInferenceSystem'),
        'continual': ('.continual_learning', 'CLTrainer'),
        'ensemble': ('.ensemble_learning', 'EnsembleTrainer'),
        'evolutionary': ('.evolutionary_computing', 'create_evolutionary_optimizer'),
        'federated': ('.federated_learning', 'FederatedLearningSystem'),
        'hpo': ('.hyperparameter_optimization', 'HpoManager'),
        'meta': ('.meta_learning', 'MetaLearner'),
        'multitask': ('.multitask_learning', 'MultiTaskTrainer'),
        'nas': ('.nas', 'EvolutionaryNAS'),
        'reinforcement': ('.reinforcement_learning', 'RLTrainingManager'),
        'self_supervised': ('.self_supervised_learning', 'SSLTrainer'),
        'transfer': ('.transfer_learning', 'TransferTrainer'),
    }

    _BUILTIN_ALIASES: Dict[str, str] = {
        'active_learning': 'active',
        'activelearner': 'active',
        'adaptive_learning': 'adaptive',
        'adaptivelearner': 'adaptive',
        'adversarial_learning': 'adversarial',
        'adversariallearner': 'adversarial',
        'bayesian_optimization': 'bayesian',
        'bayesianoptimizer': 'bayesian',
        'causal_inference': 'causal',
        'causalinference': 'causal',
        'continual_learning': 'continual',
        'continuallearner': 'continual',
        'ensemble_learning': 'ensemble',
        'ensemblelearner': 'ensemble',
        'evolutionary_computing': 'evolutionary',
        'evolutionaryoptimizer': 'evolutionary',
        'federated_learning': 'federated',
        'federatedlearner': 'federated',
        'hyperparameter_optimization': 'hpo',
        'hyperparameteroptimizer': 'hpo',
        'hpomanager': 'hpo',
        'meta_learning': 'meta',
        'metalearner': 'meta',
        'multitask_learning': 'multitask',
        'multitasklearner': 'multitask',
        'neural_architecture_search': 'nas',
        'nasoptimizer': 'nas',
        'evolutionarynas': 'nas',
        'reinforcement_learning': 'reinforcement',
        'reinforcementlearner': 'reinforcement',
        'rltrainingmanager': 'reinforcement',
        'self_supervised_learning': 'self_supervised',
        'selfsupervisedlearner': 'self_supervised',
        'ssltrainer': 'self_supervised',
        'transfer_learning': 'transfer',
        'transferlearner': 'transfer',
        'transfertrainer': 'transfer',
    }

    @classmethod
    def _resolve_name(cls, name: str) -> str:
        key = name.lower().replace('-', '_')
        resolved = cls._aliases.get(key, key)
        return cls._BUILTIN_ALIASES.get(resolved, resolved)

    @classmethod
    def get_learner(cls, name: Union[str, LearningStrategyType]) -> Any:
        """Retrieve registered learner class or factory by name or enum."""
        raw = name.value if isinstance(name, LearningStrategyType) else name
        key = cls._resolve_name(raw)
        with cls._lock:
            if key in cls._learners:
                return cls._learners[key]
            
            if key in cls._BUILTIN_LEARNERS:
                mod_path, symbol = cls._BUILTIN_LEARNERS[key]
                import importlib
                pkg = "learning" if "learning" in sys.modules else __package__
                try:
                    module = importlib.import_module(mod_path, pkg)
                except ModuleNotFoundError:
                    module = importlib.import_module(f"optimization_core.learning{mod_path}")
                obj = getattr(module, symbol)
                cls._learners[key] = obj
                return obj

        raise LearnerNotFoundError(
            f"Learner '{name}' not found in registry. "
            f"Available: {cls.list_learners()}"
        )

    @classmethod
    def get_optimizer(cls, name: Union[str, LearningStrategyType]) -> Any:
        """Retrieve registered optimizer class or factory by name or enum."""
        raw = name.value if isinstance(name, LearningStrategyType) else name
        key = cls._resolve_name(raw)
        with cls._lock:
            if key in cls._optimizers:
                return cls._optimizers[key]
            if key in cls._learners:
                return cls._learners[key]
            if key in cls._BUILTIN_LEARNERS:
                return cls.get_learner(name)
        raise StrategyNotSupportedError(
            f"Optimizer '{name}' not found in registry. "
            f"Available: {cls.list_optimizers()}"
        )

    @classmethod
    def get_strategy(cls, name: str) -> Any:
        """Retrieve registered strategy class."""
        key = cls._resolve_name(name)
        with cls._lock:
            if key in cls._strategies:
                return cls._strategies[key]
        raise StrategyNotSupportedError(
            f"Strategy '{name}' not found. Available: {cls.list_strategies()}"
        )

    @classmethod
    def get_info(cls, name: str) -> Dict[str, Any]:
        """Get metadata about a registered learning module."""
        key = cls._resolve_name(name)
        with cls._lock:
            return cls._metadata.get(key, {"name": key, "description": f"Learning module {key}"})

    @classmethod
    def list_learners(cls) -> List[str]:
        """List all registered learner identifiers."""
        with cls._lock:
            all_keys = set(cls._learners.keys()) | set(cls._BUILTIN_LEARNERS.keys())
            return sorted(list(all_keys))

    @classmethod
    def list_optimizers(cls) -> List[str]:
        """List all registered optimizer identifiers."""
        with cls._lock:
            return sorted(list(cls._optimizers.keys()))

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all registered strategy identifiers."""
        with cls._lock:
            return sorted(list(cls._strategies.keys()))

    @classmethod
    def create(
        cls,
        category: str,
        name: Union[str, LearningStrategyType],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Dynamically instantiate a registered component.
        
        Args:
            category: Component category ('learner', 'optimizer', 'strategy', 'sampler', 'callback').
            name: Component name or Enum.
            *args, **kwargs: Constructor arguments passed to component.
        """
        category = category.lower()
        if category in ("learner", "learners"):
            target = cls.get_learner(name)
        elif category in ("optimizer", "optimizers"):
            target = cls.get_optimizer(name)
        elif category in ("strategy", "strategies"):
            target = cls.get_strategy(str(name))
        else:
            raise ValueError(f"Unknown registry category: '{category}'")

        return target(*args, **kwargs)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered components (useful for testing)."""
        with cls._lock:
            cls._learners.clear()
            cls._optimizers.clear()
            cls._strategies.clear()
            cls._samplers.clear()
            cls._callbacks.clear()
            cls._aliases.clear()
            cls._metadata.clear()


# Global Singleton Alias
LEARNING_REGISTRY = LearningRegistry


# Convenience Module Functions
def register_learning_module(name: str, factory: Any, description: Optional[str] = None) -> Any:
    return LearningRegistry.register(name, factory, description=description)


def list_available_learning_modules() -> List[str]:
    return LearningRegistry.list_learners()


def get_learning_module_info(name: str) -> Dict[str, Any]:
    return LearningRegistry.get_info(name)


def create_learning_module(module_type: str, config: Any = None, **kwargs: Any) -> Any:
    """Unified factory function to instantiate any learning module."""
    learner_factory = LearningRegistry.get_learner(module_type)
    if config is not None:
        return learner_factory(config=config, **kwargs)
    return learner_factory(**kwargs)


def create_learner(strategy_type: Union[str, LearningStrategyType], config: Any = None, **kwargs: Any) -> Any:
    """Instantiate a learner using strategy type and optional configuration."""
    return create_learning_module(str(strategy_type), config=config, **kwargs)


__all__ = [
    'LearningRegistry',
    'LEARNING_REGISTRY',
    'register_learning_module',
    'list_available_learning_modules',
    'get_learning_module_info',
    'create_learning_module',
    'create_learner',
]
