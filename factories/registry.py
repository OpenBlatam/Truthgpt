"""
Registry System for Optimization Core
======================================
Generic, thread-safe object registry mapping string identifiers to classes, functions, or builder objects.
Supports metadata tracking, priority resolution, scoping, lifecycle hooks, aliases, fuzzy key matching,
tag queries, capability filtering, and dictionary export/import.
"""

import difflib
import logging
import threading
import warnings
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .base import FactoryMetadata, FactoryScope, ManagedInstance, RegistryItem
from .exceptions import (
    BuildError,
    DuplicateRegistrationError,
    KeyNotFoundError,
    RegistryError,
    TypeMismatchError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Registry(Generic[T]):
    """
    A generic, thread-safe registry mapping string keys to classes, functions, or instances.

    Supports registration via decorators or direct calls, priority resolution, scope control
    (transient/singleton/thread-local), lifecycle event callbacks, dictionary-style access,
    tag/capability querying, and fuzzy error reporting.
    """

    def __init__(self, name: str = "Registry", allow_override: bool = True) -> None:
        self.name: str = name
        self.allow_override: bool = allow_override
        self._items: Dict[str, T] = {}
        self._records: Dict[str, RegistryItem[T]] = {}
        self._instances: Dict[str, ManagedInstance[Any]] = {}
        self._aliases: Dict[str, str] = {}
        self._alias_deprecation: Dict[str, str] = {}

        # Lifecycle Event Callbacks
        self._on_register_hooks: List[Callable[[str, T], None]] = []
        self._on_build_hooks: List[Callable[[str, Any], None]] = []
        self._on_unregister_hooks: List[Callable[[str], None]] = []
        self._on_error_hooks: List[Callable[[str, Exception], None]] = []

        self._lock = threading.RLock()
        self._local_storage = threading.local()

    def add_on_register_hook(self, hook: Callable[[str, T], None]) -> None:
        """Add a callback hook invoked whenever a new item is registered."""
        with self._lock:
            self._on_register_hooks.append(hook)

    add_register_hook = add_on_register_hook

    def add_on_build_hook(self, hook: Callable[[str, Any], None]) -> None:
        """Add a callback hook invoked whenever an item is constructed."""
        with self._lock:
            self._on_build_hooks.append(hook)

    add_build_hook = add_on_build_hook

    def add_on_unregister_hook(self, hook: Callable[[str], None]) -> None:
        """Add a callback hook invoked whenever an item is removed."""
        with self._lock:
            self._on_unregister_hooks.append(hook)

    def add_on_error_hook(self, hook: Callable[[str, Exception], None]) -> None:
        """Add a callback hook invoked whenever a build or registration error occurs."""
        with self._lock:
            self._on_error_hooks.append(hook)

    def register(
        self,
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        tags: Optional[Union[List[str], Set[str]]] = None,
        scope: FactoryScope = FactoryScope.TRANSIENT,
        priority: int = 0,
        version: str = "1.0.0",
        author: str = "TruthGPT Team",
        hardware_requirements: Optional[Union[List[str], Set[str]]] = None,
        deprecation_notice: Optional[str] = None,
        deprecated: bool = False,
        deprecation_msg: Optional[str] = None,
        **metadata: Any,
    ) -> Callable[[Union[T, Callable[..., T]]], Union[T, Callable[..., T]]]:
        """
        Decorator or direct method to register an object under a specific string identifier.
        """
        if deprecated and not deprecation_notice:
            deprecation_notice = deprecation_msg or "Deprecated item."

        def decorator(obj: Union[T, Callable[..., T]]) -> Union[T, Callable[..., T]]:
            reg_name = name or getattr(obj, "__name__", str(obj))
            canonical_key = reg_name.strip()
            lower_key = canonical_key.lower()

            with self._lock:
                existing_record = self._records.get(canonical_key) or self._records.get(lower_key)
                if existing_record and not self.allow_override:
                    if priority <= existing_record.priority:
                        err = DuplicateRegistrationError(
                            key=canonical_key,
                            registry_name=self.name,
                            existing_target=str(existing_record.target),
                        )
                        self._trigger_error_hooks(canonical_key, err)
                        raise err

                record = RegistryItem(
                    name=canonical_key,
                    target=obj,
                    description=description,
                    tags=tags,
                    scope=scope,
                    priority=priority,
                    version=version,
                    author=author,
                    hardware_requirements=hardware_requirements,
                    deprecation_notice=deprecation_notice,
                    metadata=metadata,
                )

                self._items[canonical_key] = obj
                self._items[lower_key] = obj
                self._records[canonical_key] = record
                self._records[lower_key] = record

                if aliases:
                    for alias in aliases:
                        self.register_alias(
                            alias, canonical_key, deprecation_notice=deprecation_notice
                        )

                for hook in self._on_register_hooks:
                    try:
                        hook(canonical_key, obj)
                    except Exception as e:
                        logger.error(
                            f"Error in on_register hook for '{canonical_key}': {e}"
                        )

            return obj

        return decorator

    def register_alias(
        self,
        alias_name: str,
        target_name: str,
        deprecation_notice: Optional[str] = None,
    ) -> None:
        """Register an alias key pointing to an existing canonical key."""
        alias_key = alias_name.strip().lower()
        target_key = target_name.strip()

        with self._lock:
            if target_key not in self._items and target_key.lower() not in self._items:
                err = KeyNotFoundError(
                    key=target_name,
                    registry_name=self.name,
                    message=f"Cannot create alias '{alias_name}': Target '{target_name}' is not registered in {self.name}.",
                )
                self._trigger_error_hooks(alias_name, err)
                raise err

            self._aliases[alias_key] = target_key
            if deprecation_notice:
                self._alias_deprecation[alias_key] = deprecation_notice

    def get(self, name: str) -> T:
        """
        Retrieve a registered target object by name or alias.
        """
        key = name.strip()
        record = self.get_record(key)
        if record and record.metadata.is_deprecated():
            warnings.warn(
                f"Component '{key}' is deprecated: {record.metadata.deprecation_notice}",
                DeprecationWarning,
                stacklevel=2,
            )

        with self._lock:
            if key in self._items:
                return self._items[key]

            lower_key = key.lower()
            if lower_key in self._items:
                return self._items[lower_key]

            if lower_key in self._aliases:
                if lower_key in self._alias_deprecation:
                    warnings.warn(
                        f"Alias '{name}' is deprecated: {self._alias_deprecation[lower_key]}",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                target_canonical = self._aliases[lower_key]
                return self._items[target_canonical]

            available = self.keys()
            matches = difflib.get_close_matches(name, available, n=3, cutoff=0.5)
            err = KeyNotFoundError(
                key=name,
                registry_name=self.name,
                available_keys=available,
                suggestions=matches,
            )
            self._trigger_error_hooks(name, err)
            raise err

    def build(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Retrieve a registered builder or class and construct an instance with *args and **kwargs.
        """
        key = name.strip()
        record = self.get_record(name)

        if record and record.metadata.is_deprecated():
            warnings.warn(
                f"Component '{key}' is deprecated: {record.metadata.deprecation_notice}",
                DeprecationWarning,
                stacklevel=2,
            )

        with self._lock:
            # Singleton Scope Handling
            if record and record.metadata.scope == FactoryScope.SINGLETON:
                if key in self._instances:
                    return self._instances[key].touch()

            # Thread-Local Scope Handling
            if record and record.metadata.scope == FactoryScope.THREAD_LOCAL:
                if not hasattr(self._local_storage, "instances"):
                    self._local_storage.instances = {}
                if key in self._local_storage.instances:
                    return self._local_storage.instances[key]

            cls_or_fn = self.get(name)
            try:
                if callable(cls_or_fn):
                    instance = cls_or_fn(*args, **kwargs)
                else:
                    instance = cls_or_fn
            except Exception as exc:
                err = BuildError(key=name, cause=exc, registry_name=self.name)
                self._trigger_error_hooks(name, err)
                raise err from exc

            # Cache singletons
            if record and record.metadata.scope == FactoryScope.SINGLETON:
                self._instances[key] = ManagedInstance(instance)

            # Cache thread-locals
            if record and record.metadata.scope == FactoryScope.THREAD_LOCAL:
                self._local_storage.instances[key] = instance

            for hook in self._on_build_hooks:
                try:
                    hook(key, instance)
                except Exception as e:
                    logger.error(f"Error in on_build hook for '{key}': {e}")

            return instance

    def get_record(self, name: str) -> Optional[RegistryItem[T]]:
        """Retrieve full RegistryItem metadata object for a given key or alias."""
        key = name.strip()
        with self._lock:
            if key in self._records:
                return self._records[key]
            lower_key = key.lower()
            if lower_key in self._records:
                return self._records[lower_key]
            if lower_key in self._aliases:
                return self._records.get(self._aliases[lower_key])
            return None

    def inspect(self, name: str) -> Dict[str, Any]:
        """Return structured inspection record of a registered item."""
        record = self.get_record(name)
        if not record:
            raise KeyNotFoundError(key=name, registry_name=self.name)
        return record.metadata.to_dict()

    def list_by_tag(self, tag: str) -> List[str]:
        """Return names of registered items tagged with the specified tag."""
        with self._lock:
            tag_lower = tag.strip().lower()
            return [
                rec.name
                for rec in self._records.values()
                if any(t.lower() == tag_lower for t in rec.metadata.tags)
            ]

    def search(self, query: str) -> List[str]:
        """Search registered names, aliases, and descriptions matching query substring."""
        query_lower = query.strip().lower()
        with self._lock:
            results = set()
            for record in self._records.values():
                name_match = query_lower in record.name.lower()
                desc_match = (
                    record.metadata.description
                    and query_lower in record.metadata.description.lower()
                )
                tag_match = any(query_lower in t.lower() for t in record.metadata.tags)
                if name_match or desc_match or tag_match:
                    results.add(record.name)
            for alias, target in self._aliases.items():
                if query_lower in alias.lower() and target in self._records:
                    results.add(self._records[target].name)
            return list(results)

    def find_by_capability(self, capability: str) -> List[str]:
        """Return items matching required hardware or capability tags."""
        with self._lock:
            cap_lower = capability.strip().lower()
            return [
                rec.name
                for rec in self._records.values()
                if any(c.lower() == cap_lower for c in rec.metadata.hardware_requirements)
            ]

    def keys(self) -> List[str]:
        """Return unique registered canonical keys."""
        with self._lock:
            seen = set()
            result = []
            for record in self._records.values():
                if record.name not in seen:
                    seen.add(record.name)
                    result.append(record.name)
            return result

    def values(self) -> List[T]:
        """Return unique registered objects."""
        with self._lock:
            seen_ids = set()
            result = []
            for record in self._records.values():
                obj_id = id(record.target)
                if obj_id not in seen_ids:
                    seen_ids.add(obj_id)
                    result.append(record.target)
            return result

    def items(self) -> List[Tuple[str, T]]:
        """Return list of (canonical_key, object) tuples."""
        with self._lock:
            seen = set()
            result = []
            for record in self._records.values():
                if record.name not in seen:
                    seen.add(record.name)
                    result.append((record.name, record.target))
            return result

    def unregister(self, name: str) -> None:
        """Remove an item and its aliases from registry."""
        key = name.strip()
        with self._lock:
            lower_key = key.lower()
            self._items.pop(key, None)
            self._items.pop(lower_key, None)
            self._records.pop(key, None)
            self._records.pop(lower_key, None)
            self._instances.pop(key, None)
            self._instances.pop(lower_key, None)

            aliases_to_remove = [
                alias
                for alias, target in self._aliases.items()
                if target == key or target.lower() == lower_key
            ]
            for alias in aliases_to_remove:
                self._aliases.pop(alias, None)
                self._alias_deprecation.pop(alias, None)

            for hook in self._on_unregister_hooks:
                try:
                    hook(key)
                except Exception as e:
                    logger.error(f"Error in on_unregister hook for '{key}': {e}")

    def clear(self) -> None:
        """Clear all registered items, metadata, aliases, and cached instances."""
        with self._lock:
            self._items.clear()
            self._records.clear()
            self._instances.clear()
            self._aliases.clear()
            self._alias_deprecation.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export registry items and metadata to a dictionary representation."""
        with self._lock:
            return {
                "registry_name": self.name,
                "item_count": len(self),
                "items": {name: self.inspect(name) for name in self.keys()},
                "aliases": dict(self._aliases),
            }

    def _trigger_error_hooks(self, key: str, exc: Exception) -> None:
        """Execute registered error handler hooks."""
        for hook in self._on_error_hooks:
            try:
                hook(key, exc)
            except Exception as e:
                logger.error(f"Error in on_error hook for '{key}': {e}")

    def __contains__(self, name: str) -> bool:
        key = name.strip()
        lower_key = key.lower()
        with self._lock:
            return (
                key in self._items
                or lower_key in self._items
                or lower_key in self._aliases
            )

    def __getitem__(self, name: str) -> T:
        return self.get(name)

    def __len__(self) -> int:
        return len(self.values())

    def __repr__(self) -> str:
        return f"<{self.name}: {len(self)} items, {len(self._aliases)} aliases>"


__all__ = ["Registry"]
