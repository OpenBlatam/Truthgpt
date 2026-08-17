"""
Base Dynamic Adapter Implementation — Pydantic-First & Protocol Architecture.

This module provides the BaseDynamicAdapter and BaseAdapter classes, bridging procedural
adapters into the autonomous ToolRegistry ecosystem (BaseTool), along with a thread-safe,
in-memory ObjectStore for managing stateful Python objects across adapter components.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, Union, runtime_checkable

from pydantic import BaseModel, Field, computed_field

try:
    from optimization_core.agents.framework.tools.tools import BaseTool, ToolResult
except Exception:
    try:
        from agents.framework.tools.tools import BaseTool, ToolResult
    except Exception:
        BaseTool, ToolResult = None, None

logger: logging.Logger = logging.getLogger(__name__)

T_in = TypeVar("T_in")
T_out = TypeVar("T_out")


# ---------------------------------------------------------------------------
# Exception Hierarchy
# ---------------------------------------------------------------------------

class AdapterError(Exception):
    """Base exception class for all adapter operations in optimization_core."""
    pass


class ObjectNotFoundError(AdapterError, KeyError):
    """Raised when an object requested from ObjectStore is not found or expired."""
    pass


class AdapterConfigurationError(AdapterError, ValueError):
    """Raised when an adapter configuration is invalid or missing required parameters."""
    pass


class AdapterExecutionError(AdapterError, RuntimeError):
    """Raised when adapter processing or execution fails."""
    pass


# ---------------------------------------------------------------------------
# Protocols & Interfaces
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseAdapterProtocol(Protocol):
    """Formal runtime protocol for adapter components across optimization_core."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input parameters and produce adapted dictionary output.

        Args:
            input_data: Key-value configuration or runtime parameters.

        Returns:
            Adapted dictionary output payload.
        """
        ...


# ---------------------------------------------------------------------------
# Pydantic Response & State Models
# ---------------------------------------------------------------------------

class ObjectEntry(BaseModel):
    """Typed metadata record for an object stored in ObjectStore."""
    obj_id: str = Field(description="Unique identifier for the stored object")
    kind: str = Field(default="unknown", description="Category or kind of stored object")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata dictionary")
    stored_at: float = Field(default_factory=time.time, description="POSIX timestamp when stored")
    ttl_seconds: Optional[float] = Field(default=None, description="Optional time-to-live in seconds before expiration")

    @computed_field  # type: ignore[misc]
    @property
    def age_seconds(self) -> float:
        """Calculate age of stored entry in seconds."""
        return round(time.time() - self.stored_at, 2)

    @computed_field  # type: ignore[misc]
    @property
    def is_expired(self) -> bool:
        """Check whether the entry has exceeded its time-to-live threshold."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.stored_at) > self.ttl_seconds


class StoreStats(BaseModel):
    """Snapshot summary of the ObjectStore state."""
    total_objects: int = Field(default=0, description="Total count of active objects in store")
    kinds: Dict[str, int] = Field(default_factory=dict, description="Object counts grouped by kind")
    expired_count: int = Field(default=0, description="Count of expired objects currently in store")


class AdapterRunResult(BaseModel):
    """Structured metadata from a BaseDynamicAdapter execution."""
    adapter_name: str = Field(description="Name of the adapter executed")
    status: str = Field(description="Status of execution ('success' | 'error')")
    elapsed_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    input_keys: List[str] = Field(default_factory=list, description="Keys present in input payload")


# ---------------------------------------------------------------------------
# Process-Global Thread-Safe Object Store
# ---------------------------------------------------------------------------

class ObjectStore:
    """
    Thread-safe, in-memory object store for heavyweight Python objects (models,
    datasets, optimizers, trainers) managed across adapters.
    """

    _singleton: Optional[ObjectStore] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._objects: Dict[str, Any] = {}
        self._entries: Dict[str, ObjectEntry] = {}
        self._obj_lock: threading.Lock = threading.Lock()

    @classmethod
    def instance(cls) -> ObjectStore:
        """Return the process-global ObjectStore singleton instance."""
        if cls._singleton is None:
            with cls._lock:
                if cls._singleton is None:
                    cls._singleton = cls()
        return cls._singleton

    def put(
        self,
        obj: Any,
        *,
        kind: str = "unknown",
        meta: Optional[Dict[str, Any]] = None,
        custom_id: Optional[str] = None,
        ttl_seconds: Optional[float] = None,
    ) -> str:
        """
        Store an object in memory and return a unique string ID handle.

        Args:
            obj: Python object instance to store.
            kind: Classification string (e.g. 'model', 'dataset', 'optimizer').
            meta: Optional metadata dictionary.
            custom_id: Optional custom string handle to use instead of generating a UUID.
            ttl_seconds: Optional time-to-live in seconds.

        Returns:
            Unique string identifier handle.
        """
        obj_id = custom_id or f"{kind}_{uuid.uuid4().hex[:12]}"
        entry = ObjectEntry(
            obj_id=obj_id,
            kind=kind,
            meta=meta or {},
            ttl_seconds=ttl_seconds,
        )
        with self._obj_lock:
            self._objects[obj_id] = obj
            self._entries[obj_id] = entry
        logger.info("ObjectStore: stored %s (kind=%s)", obj_id, kind)
        return obj_id

    def get(self, obj_id: str) -> Any:
        """
        Retrieve raw object by unique object identifier.

        Args:
            obj_id: Unique handle string returned from put().

        Returns:
            Stored Python object reference.

        Raises:
            ObjectNotFoundError: If obj_id is not present in the store or has expired.
        """
        with self._obj_lock:
            entry = self._entries.get(obj_id)
            if entry is not None and entry.is_expired:
                self._objects.pop(obj_id, None)
                self._entries.pop(obj_id, None)
                entry = None

            obj = self._objects.get(obj_id)

        if obj is None:
            with self._obj_lock:
                available = list(self._objects.keys())
            raise ObjectNotFoundError(f"ObjectStore: ID '{obj_id}' not found. Available IDs: {available}")
        return obj

    def get_optional(self, obj_id: str, default: Any = None) -> Any:
        """
        Retrieve object by obj_id, or return default if not found or expired.

        Args:
            obj_id: Unique handle string.
            default: Default value if handle is missing.

        Returns:
            Stored object or default value.
        """
        try:
            return self.get(obj_id)
        except ObjectNotFoundError:
            return default

    def has(self, obj_id: str) -> bool:
        """
        Check if an active, non-expired object ID exists in the store.

        Args:
            obj_id: Unique handle string.

        Returns:
            True if object exists and is not expired, False otherwise.
        """
        with self._obj_lock:
            entry = self._entries.get(obj_id)
            if entry is None:
                return False
            if entry.is_expired:
                self._objects.pop(obj_id, None)
                self._entries.pop(obj_id, None)
                return False
            return obj_id in self._objects

    def get_entry(self, obj_id: str) -> ObjectEntry:
        """
        Return typed ObjectEntry record for obj_id.

        Args:
            obj_id: Unique handle string.

        Returns:
            ObjectEntry model instance containing metadata.

        Raises:
            ObjectNotFoundError: If obj_id is not found in store or is expired.
        """
        with self._obj_lock:
            entry = self._entries.get(obj_id)
            if entry is not None and entry.is_expired:
                self._objects.pop(obj_id, None)
                self._entries.pop(obj_id, None)
                entry = None

        if entry is None:
            raise ObjectNotFoundError(f"ObjectStore: ID '{obj_id}' not found in entries.")
        return entry

    def get_meta(self, obj_id: str) -> Dict[str, Any]:
        """
        Return metadata dictionary attached to stored object.

        Args:
            obj_id: Unique handle string.

        Returns:
            Dictionary of metadata parameters.
        """
        return self.get_entry(obj_id).meta

    def delete(self, obj_id: str) -> bool:
        """
        Remove an object and associated metadata entry from the store.

        Args:
            obj_id: Unique handle string.

        Returns:
            True if object was found and removed, False otherwise.
        """
        with self._obj_lock:
            removed_obj = self._objects.pop(obj_id, None)
            self._entries.pop(obj_id, None)
        if removed_obj is not None:
            logger.info("ObjectStore: deleted %s", obj_id)
            return True
        return False

    def list_ids(self, kind: Optional[str] = None) -> List[str]:
        """
        Return list of stored active object IDs, optionally filtered by kind.

        Args:
            kind: Optional classification string filter.

        Returns:
            List of object ID strings.
        """
        self.prune_expired()
        with self._obj_lock:
            if kind:
                return [k for k, e in self._entries.items() if e.kind == kind]
            return list(self._entries.keys())

    def list_entries(self, kind: Optional[str] = None) -> List[ObjectEntry]:
        """
        Return list of ObjectEntry records for active objects, optionally filtered by kind.

        Args:
            kind: Optional classification string filter.

        Returns:
            List of ObjectEntry model instances.
        """
        self.prune_expired()
        with self._obj_lock:
            entries = list(self._entries.values())
        if kind:
            entries = [e for e in entries if e.kind == kind]
        return entries

    def prune_expired(self) -> int:
        """
        Remove all expired entries from the store.

        Returns:
            Number of pruned expired entries.
        """
        with self._obj_lock:
            expired_ids = [k for k, e in self._entries.items() if e.is_expired]
            for obj_id in expired_ids:
                self._objects.pop(obj_id, None)
                self._entries.pop(obj_id, None)
            if expired_ids:
                logger.info("ObjectStore: pruned %d expired objects", len(expired_ids))
            return len(expired_ids)

    def stats(self) -> StoreStats:
        """
        Return a typed snapshot summary of store statistics.

        Returns:
            StoreStats model instance.
        """
        with self._obj_lock:
            kinds: Dict[str, int] = {}
            expired_count = 0
            for e in self._entries.values():
                if e.is_expired:
                    expired_count += 1
                else:
                    kinds[e.kind] = kinds.get(e.kind, 0) + 1
            return StoreStats(
                total_objects=len(self._entries) - expired_count,
                kinds=kinds,
                expired_count=expired_count,
            )

    def clear(self) -> int:
        """
        Clear all stored objects and return the count of cleared items.

        Returns:
            Integer count of cleared objects.
        """
        with self._obj_lock:
            count = len(self._objects)
            self._objects.clear()
            self._entries.clear()
        logger.info("ObjectStore: cleared %d objects", count)
        return count

    def get_by_kind(self, kind: str) -> Dict[str, Any]:
        """
        Retrieve all stored raw active objects matching a specified kind.

        Args:
            kind: Target classification string.

        Returns:
            Dictionary mapping object ID strings to object references.
        """
        self.prune_expired()
        with self._obj_lock:
            target_ids = [k for k, e in self._entries.items() if e.kind == kind]
            return {obj_id: self._objects[obj_id] for obj_id in target_ids if obj_id in self._objects}

    def clear_kind(self, kind: str) -> int:
        """
        Remove all stored objects matching a specific kind classification.

        Args:
            kind: Target classification string.

        Returns:
            Integer count of removed objects.
        """
        with self._obj_lock:
            target_ids = [k for k, e in self._entries.items() if e.kind == kind]
            for obj_id in target_ids:
                self._objects.pop(obj_id, None)
                self._entries.pop(obj_id, None)
            count = len(target_ids)
        logger.info("ObjectStore: cleared %d objects of kind '%s'", count, kind)
        return count


# ---------------------------------------------------------------------------
# Base Adapter Lifecycle Abstract Class
# ---------------------------------------------------------------------------

class BaseAdapter(ABC, Generic[T_in, T_out]):
    """Generic base class for typed adapters with complete lifecycle management."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name: str = name or self.__class__.__name__
        self._is_initialized: bool = False

    def initialize(self) -> None:
        """Initialize adapter resources."""
        self._is_initialized = True

    def cleanup(self) -> None:
        """Release adapter resources."""
        self._is_initialized = False

    def health_check(self) -> bool:
        """Verify initialization health state of adapter."""
        return self._is_initialized

    @abstractmethod
    def adapt(self, input_data: T_in) -> T_out:
        """Core adaptation logic to be implemented by concrete adapters."""
        pass

    async def adapt_async(self, input_data: T_in) -> T_out:
        """Asynchronous adaptation execution wrapper.

        Args:
            input_data: Input data structure.

        Returns:
            Adapted output structure.
        """
        return self.adapt(input_data)

    async def transform(self, input_data: T_in) -> T_out:
        """Standardized async transform pipeline stage.

        Args:
            input_data: Input data payload.

        Returns:
            Transformed output payload.
        """
        if not self._is_initialized:
            self.initialize()
        return await self.adapt_async(input_data)

    async def execute(self, input_data: T_in) -> T_out:
        """Standardized async execution pipeline stage.

        Args:
            input_data: Input data payload.

        Returns:
            Executed output payload.
        """
        return await self.transform(input_data)

    def __enter__(self) -> BaseAdapter[T_in, T_out]:
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()

    async def __aenter__(self) -> BaseAdapter[T_in, T_out]:
        self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()


_BaseToolClass = BaseTool if BaseTool is not None else object


class BaseDynamicAdapter(_BaseToolClass, BaseAdapter[Dict[str, Any], Dict[str, Any]]):  # type: ignore[misc]
    """Base class for dynamic intelligence adapters integrating into BaseTool framework."""

    @property
    def store(self) -> ObjectStore:
        """Convenience accessor to global ObjectStore singleton."""
        return ObjectStore.instance()

    def adapt(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate adaptation call to process().

        Args:
            input_data: Dictionary payload.

        Returns:
            Dictionary response output.
        """
        return self.process(input_data)

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Core dynamic processing logic to be implemented by subclasses.

        Args:
            input_data: Key-value dictionary payload.

        Returns:
            Response payload dictionary.
        """
        pass

    async def run(self, tool_input: str) -> Any:
        """
        Tool execution entry point parsing stringified JSON input payload.

        Args:
            tool_input: String containing JSON formatted payload.

        Returns:
            ToolResult instance if BaseTool available, else dictionary output.
        """
        start = time.monotonic()
        name_attr = getattr(self, "name", self.__class__.__name__)
        try:
            input_data = json.loads(tool_input)
            if not isinstance(input_data, dict):
                raise AdapterConfigurationError("JSON payload must be a key-value dictionary.")

            input_keys = list(input_data.keys())
            logger.info("Adapter '%s' executing with input keys: %s", name_attr, input_keys)

            output_data = self.process(input_data)

            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            result_str = json.dumps(output_data, indent=2, default=str)
            run_result = AdapterRunResult(
                adapter_name=name_attr,
                status="success",
                elapsed_ms=elapsed_ms,
                input_keys=input_keys,
            )
            if ToolResult is not None:
                return ToolResult(
                    output=result_str,
                    metadata=run_result.model_dump(),
                )
            return output_data
        except json.JSONDecodeError as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            logger.error("Adapter '%s' failed to parse JSON input: %s", name_attr, exc)
            err_result = AdapterRunResult(
                adapter_name=name_attr,
                status="error",
                elapsed_ms=elapsed_ms,
            ).model_dump()
            if ToolResult is not None:
                return ToolResult(
                    output=f"Error: Invalid JSON input provided to {name_attr}. Details: {exc}",
                    metadata=err_result,
                )
            return {"error": str(exc), "metadata": err_result}
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            logger.exception("Adapter '%s' execution failed", name_attr)
            err_result = AdapterRunResult(
                adapter_name=name_attr,
                status="error",
                elapsed_ms=elapsed_ms,
            ).model_dump()
            if ToolResult is not None:
                return ToolResult(
                    output=f"Error during {name_attr} execution: {exc}",
                    metadata=err_result,
                )
            return {"error": str(exc), "metadata": err_result}


# Dual registration in sys.modules for smooth module resolution
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.base"] = _mod
    sys.modules["optimization_core.adapters.base"] = _mod


__all__ = [
    "AdapterError",
    "ObjectNotFoundError",
    "AdapterConfigurationError",
    "AdapterExecutionError",
    "BaseAdapterProtocol",
    "ObjectEntry",
    "StoreStats",
    "AdapterRunResult",
    "ObjectStore",
    "BaseAdapter",
    "BaseDynamicAdapter",
]
