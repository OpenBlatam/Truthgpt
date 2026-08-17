"""
Dataset Registry Module.

Provides a thread-safe centralized registry for dataset builder functions and metadata tracking.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DatasetRegistry:
    """Thread-safe dataset builder registry."""

    def __init__(self):
        self._builders: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def register(
        self,
        name_or_fn: Union[str, Callable[[Dict[str, Any]], Any]],
        description: str = "",
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
    ):
        """
        Register a dataset builder function with optional metadata.

        Args:
            name_or_fn: Unique string name or direct callable function.
            description: Description of the dataset builder.
            tags: Categorization tags.
            version: Version string.

        Returns:
            Decorator function or registered function.
        """
        def _register_internal(name: str, fn: Callable[[Dict[str, Any]], Any]):
            with self._lock:
                if name in self._builders:
                    logger.warning(f"Overwriting existing dataset builder for '{name}'")
                self._builders[name] = fn
                self._metadata[name] = {
                    "name": name,
                    "description": description or (getattr(fn, "__doc__", "") or "").strip(),
                    "tags": tags or [],
                    "version": version,
                    "module": getattr(fn, "__module__", "custom"),
                    "target": getattr(fn, "__name__", str(fn)),
                }
                return fn

        if callable(name_or_fn):
            fn = name_or_fn
            name = fn.__name__
            return _register_internal(name, fn)

        if not name_or_fn or not isinstance(name_or_fn, str):
            raise ValueError("Dataset name must be a non-empty string or a callable")

        name = name_or_fn

        def _wrap(fn: Callable[[Dict[str, Any]], Any]) -> Callable[[Dict[str, Any]], Any]:
            return _register_internal(name, fn)

        return _wrap

    def unregister(self, name: str) -> bool:
        """Unregister a dataset builder by name."""
        with self._lock:
            if name in self._builders:
                del self._builders[name]
                self._metadata.pop(name, None)
                logger.debug(f"Unregistered dataset builder: '{name}'")
                return True
            return False

    def build(self, name: str, cfg: Optional[Dict[str, Any]] = None) -> Any:
        """Build a dataset using a registered builder function."""
        if cfg is None:
            cfg = {}
        with self._lock:
            if name not in self._builders:
                available = list(self._builders.keys())
                raise KeyError(f"Dataset '{name}' is not registered. Available datasets: {available}")
            builder = self._builders[name]
        return builder(cfg)

    def has(self, name: str) -> bool:
        """Check if a dataset builder is registered by name."""
        with self._lock:
            return name in self._builders

    def list_datasets(self) -> List[str]:
        """Return a list of all registered dataset builder names."""
        with self._lock:
            return list(self._builders.keys())

    def get_builder(self, name: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        """Retrieve a registered dataset builder function if present."""
        with self._lock:
            return self._builders.get(name)

    def get_info(self, name: str) -> Dict[str, Any]:
        """Get registered dataset metadata information."""
        with self._lock:
            if name not in self._metadata:
                if name in self._builders:
                    fn = self._builders[name]
                    return {
                        "name": name,
                        "description": (getattr(fn, "__doc__", "") or "").strip(),
                        "tags": [],
                        "version": "1.0.0",
                        "module": getattr(fn, "__module__", "custom"),
                        "target": getattr(fn, "__name__", str(fn)),
                    }
                raise KeyError(f"Dataset '{name}' is not registered.")
            return dict(self._metadata[name])

    def clear(self) -> None:
        """Clear all registered dataset builders and metadata."""
        with self._lock:
            self._builders.clear()
            self._metadata.clear()
            logger.debug("Cleared dataset registry")


# Default global instance
default_registry = DatasetRegistry()

# Function delegators for backward compatibility
register_dataset = default_registry.register
unregister_dataset = default_registry.unregister
build_dataset = default_registry.build
has_dataset = default_registry.has
list_registered_datasets = default_registry.list_datasets
get_dataset_builder = default_registry.get_builder
get_dataset_info = default_registry.get_info
clear_dataset_registry = default_registry.clear


__all__ = [
    "DatasetRegistry",
    "default_registry",
    "register_dataset",
    "unregister_dataset",
    "build_dataset",
    "has_dataset",
    "list_registered_datasets",
    "get_dataset_builder",
    "get_dataset_info",
    "clear_dataset_registry",
]
