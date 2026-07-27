"""
Thread-safe dynamic component registry for trainers module.

Allows runtime registration and discovery of custom callbacks, optimizers, trackers,
and manager components for enterprise extensibility.
"""
import threading
from typing import Dict, Any, Type, Callable, Optional, List


class TrainerRegistry:
    """Central registry for extensible trainer components."""
    _lock = threading.Lock()
    _callbacks: Dict[str, Type[Any]] = {}
    _optimizers: Dict[str, Type[Any]] = {}
    _trackers: Dict[str, Type[Any]] = {}
    _datasets: Dict[str, Type[Any]] = {}

    @classmethod
    def register_callback(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Callback class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._callbacks[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def register_optimizer(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Optimizer class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._optimizers[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def register_tracker(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom ExperimentTracker class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._trackers[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def register_dataset(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Dataset class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._datasets[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_callback(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered callback class by name."""
        with cls._lock:
            return cls._callbacks.get(name.lower())

    @classmethod
    def get_optimizer(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered optimizer class by name."""
        with cls._lock:
            return cls._optimizers.get(name.lower())

    @classmethod
    def get_tracker(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered tracker class by name."""
        with cls._lock:
            return cls._trackers.get(name.lower())

    @classmethod
    def get_dataset(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered dataset class by name."""
        with cls._lock:
            return cls._datasets.get(name.lower())

    @classmethod
    def list_callbacks(cls) -> List[str]:
        """List names of all registered callbacks."""
        with cls._lock:
            return list(cls._callbacks.keys())

    @classmethod
    def list_optimizers(cls) -> List[str]:
        """List names of all registered optimizers."""
        with cls._lock:
            return list(cls._optimizers.keys())

    @classmethod
    def list_trackers(cls) -> List[str]:
        """List names of all registered trackers."""
        with cls._lock:
            return list(cls._trackers.keys())

    @classmethod
    def list_datasets(cls) -> List[str]:
        """List names of all registered datasets."""
        with cls._lock:
            return list(cls._datasets.keys())


__all__ = ["TrainerRegistry"]
