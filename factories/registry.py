"""
Registry System for Optimization Core
======================================
Generic object registry mapping string identifiers to classes, functions, or builder objects.
"""
import difflib
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

import threading

T = TypeVar("T")


class Registry(Generic[T]):
    """
    A generic, thread-safe registry mapping string keys to classes, functions, or instances.
    
    Supports registration via decorators, dictionary-style access, iteration,
    and helpful error reporting when keys are missing.
    """

    def __init__(self, name: str = "Registry") -> None:
        self.name: str = name
        self._items: Dict[str, T] = {}
        self._lock = threading.Lock()

    def register(
        self, name: Optional[str] = None
    ) -> Callable[[Union[T, Callable[..., T]]], Union[T, Callable[..., T]]]:
        """
        Decorator to register an object under a specific key.
        
        Args:
            name: Optional name key. If None, uses `obj.__name__`.
        """
        def decorator(obj: Union[T, Callable[..., T]]) -> Union[T, Callable[..., T]]:
            reg_name = name or getattr(obj, "__name__", str(obj))
            key = reg_name.lower().strip()
            with self._lock:
                self._items[key] = obj  # Store under canonical key
                self._items[reg_name] = obj  # Store under original key as well
            return obj

        return decorator


    def get(self, name: str) -> T:
        """
        Retrieve a registered item by name.
        
        Args:
            name: Name of the registered item.
            
        Returns:
            The registered item.
            
        Raises:
            KeyError: If item is not registered.
        """
        key = name.strip()
        if key in self._items:
            return self._items[key]
        
        lower_key = key.lower()
        if lower_key in self._items:
            return self._items[lower_key]
            
        available = self.keys()
        matches = difflib.get_close_matches(name, available, n=3, cutoff=0.5)
        hint = f" Did you mean: {', '.join(matches)}?" if matches else ""
        raise KeyError(
            f"Item '{name}' not found in {self.name}. "
            f"Available items: {', '.join(available)}.{hint}"
        )

    def build(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Retrieve and call a registered builder or class.
        
        Args:
            name: Name of the registered item.
            *args, **kwargs: Arguments passed to the builder or class.
            
        Returns:
            Constructed object.
        """
        cls_or_fn = self.get(name)
        if callable(cls_or_fn):
            return cls_or_fn(*args, **kwargs)
        return cls_or_fn

    def keys(self) -> List[str]:
        """Return unique registered keys."""
        # Preserve original/canonical keys cleanly
        seen = set()
        result = []
        for k in self._items.keys():
            if k not in seen:
                seen.add(k)
                result.append(k)
        return result

    def items(self) -> List[tuple]:
        """Return list of (key, item) tuples."""
        return [(k, v) for k, v in self._items.items()]

    def values(self) -> List[T]:
        """Return list of unique registered items."""
        return list(set(self._items.values()))

    def unregister(self, name: str) -> None:
        """Remove an item from registry."""
        key = name.strip()
        self._items.pop(key, None)
        self._items.pop(key.lower(), None)

    def clear(self) -> None:
        """Clear all registered items."""
        self._items.clear()

    def __contains__(self, name: str) -> bool:
        key = name.strip()
        return key in self._items or key.lower() in self._items

    def __getitem__(self, name: str) -> T:
        return self.get(name)

    def __len__(self) -> int:
        return len(self.values())

    def __repr__(self) -> str:
        return f"<{self.name}: {len(self)} registered items>"






