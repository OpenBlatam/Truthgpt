"""
Factory Base Types and Metadata Containers
==========================================
Data structures for factory scopes, metadata tracking, registry items, managed instances, and abstract base factories.
"""

import inspect
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar, Union

T = TypeVar("T")


class FactoryScope(Enum):
    """Scope and caching lifecycle strategy of instantiated factory items."""

    TRANSIENT = "transient"  # Re-built on every instantiation call
    SINGLETON = "singleton"  # Instantiated once per registry and cached globally
    THREAD_LOCAL = "thread_local"  # Instantiated once per thread
    CONTEXTUAL = "contextual"  # Scoped to context manager lifetime


@dataclass
class FactoryMetadata:
    """
    Rich metadata container for registered factory components.

    Attributes:
        name: Canonical registration identifier name.
        description: Docstring or natural language summary of the component.
        tags: Set of tags for querying and categorizing components.
        scope: Instantiation scope (transient, singleton, thread-local, contextual).
        priority: Selection priority weight (higher priority is preferred in lookup).
        version: Version string for API stability tracking.
        author: Origin author or maintainer name.
        hardware_requirements: Required host hardware tags (e.g. 'cuda', 'bf16', 'triton').
        deprecation_notice: Optional warning message if component is deprecated.
        signature: Inspect signature string of target builder or class.
        registered_at: POSIX timestamp of registration time.
        extra: Additional key-value metadata attributes.
    """

    name: str
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    scope: FactoryScope = FactoryScope.TRANSIENT
    priority: int = 0
    version: str = "1.0.0"
    author: str = "TruthGPT Team"
    hardware_requirements: Set[str] = field(default_factory=set)
    deprecation_notice: Optional[str] = None
    registered_at: float = field(default_factory=time.time)
    signature: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def is_deprecated(self) -> bool:
        """Return True if component is marked with a deprecation notice."""
        return self.deprecation_notice is not None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata object to clean dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
            "scope": self.scope.value,
            "priority": self.priority,
            "version": self.version,
            "author": self.author,
            "hardware_requirements": list(self.hardware_requirements),
            "deprecation_notice": self.deprecation_notice,
            "registered_at": self.registered_at,
            "signature": self.signature,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactoryMetadata":
        """Deserialize metadata object from dictionary representation."""
        scope_val = data.get("scope", "transient")
        try:
            scope = FactoryScope(scope_val)
        except ValueError:
            scope = FactoryScope.TRANSIENT

        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            tags=set(data.get("tags", [])),
            scope=scope,
            priority=data.get("priority", 0),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "TruthGPT Team"),
            hardware_requirements=set(data.get("hardware_requirements", [])),
            deprecation_notice=data.get("deprecation_notice"),
            registered_at=data.get("registered_at", time.time()),
            signature=data.get("signature"),
            extra=data.get("extra", {}),
        )


class RegistryItem(Generic[T]):
    """
    Encapsulated wrapper holding a registered target object and its metadata.
    """

    def __init__(
        self,
        name: str,
        target: T,
        description: Optional[str] = None,
        tags: Optional[Union[List[str], Set[str]]] = None,
        scope: FactoryScope = FactoryScope.TRANSIENT,
        priority: int = 0,
        version: str = "1.0.0",
        author: str = "TruthGPT Team",
        hardware_requirements: Optional[Union[List[str], Set[str]]] = None,
        deprecation_notice: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name: str = name
        self.target: T = target

        doc = inspect.getdoc(target) if hasattr(target, "__doc__") else ""
        desc = description or doc or "No description provided."

        sig = None
        if callable(target):
            try:
                sig = str(inspect.signature(target))
            except (ValueError, TypeError):
                sig = "(...)"

        tags_set = set(tags) if tags else set()
        hw_set = set(hardware_requirements) if hardware_requirements else set()

        self.metadata: FactoryMetadata = FactoryMetadata(
            name=name,
            description=desc,
            tags=tags_set,
            scope=scope,
            priority=priority,
            version=version,
            author=author,
            hardware_requirements=hw_set,
            deprecation_notice=deprecation_notice,
            signature=sig,
            extra=metadata or {},
        )

    @property
    def priority(self) -> int:
        """Accessor for registry item priority."""
        return self.metadata.priority

    def to_dict(self) -> Dict[str, Any]:
        """Serialize item and metadata to dictionary format."""
        return {
            "name": self.name,
            "target": repr(self.target),
            "metadata": self.metadata.to_dict(),
        }

    def __repr__(self) -> str:
        return f"<RegistryItem '{self.name}' priority={self.metadata.priority} scope={self.metadata.scope.value} target={self.target!r}>"


@dataclass
class ManagedInstance(Generic[T]):
    """Wrapper holding a cached instance alongside instantiation metrics."""

    instance: T
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def touch(self) -> T:
        """Update access timestamps and count, returning the managed instance."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.instance


class BaseFactory(ABC, Generic[T]):
    """Abstract Base Class for specialized component factories."""

    @abstractmethod
    def build(self, name: str, *args: Any, **kwargs: Any) -> T:
        """Construct or retrieve a component instance by string identifier."""
        pass

    def __call__(self, name: str, *args: Any, **kwargs: Any) -> T:
        """Allow direct calling of factory instance as a builder."""
        return self.build(name, *args, **kwargs)


__all__ = [
    "FactoryScope",
    "FactoryMetadata",
    "RegistryItem",
    "ManagedInstance",
    "BaseFactory",
]
