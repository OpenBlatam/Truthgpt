"""
Base Dynamic Adapter Implementation — Pydantic-First & Protocol Architecture.

This module provides the BaseDynamicAdapter and BaseAdapter classes, bridging procedural
adapters into the autonomous ToolRegistry ecosystem (BaseTool).
"""

import logging
import json
import time
import threading
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Generic, TypeVar, runtime_checkable

from pydantic import BaseModel, Field, computed_field

import sys

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.base"] = _mod
    sys.modules["optimization_core.adapters.base"] = _mod

try:
    from optimization_core.agents.framework.tools.tools import BaseTool, ToolResult
except Exception:
    try:
        from agents.framework.tools.tools import BaseTool, ToolResult
    except Exception:
        BaseTool, ToolResult = None, None

logger = logging.getLogger(__name__)




T_in = TypeVar("T_in")
T_out = TypeVar("T_out")


# ---------------------------------------------------------------------------
# Protocols & Interfaces
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseAdapterProtocol(Protocol):
    """Formal protocol for adapter components across optimization_core."""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input parameters and produce adapted output."""
        ...


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ObjectEntry(BaseModel):
    """Typed metadata for an object stored in the ObjectStore."""
    obj_id: str
    kind: str = "unknown"
    meta: Dict[str, Any] = Field(default_factory=dict)
    stored_at: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[misc]
    @property
    def age_seconds(self) -> float:
        return round(time.time() - self.stored_at, 2)


class StoreStats(BaseModel):
    """Snapshot of the ObjectStore state."""
    total_objects: int = 0
    kinds: Dict[str, int] = Field(default_factory=dict)


class AdapterRunResult(BaseModel):
    """Structured metadata from a BaseDynamicAdapter execution."""
    adapter_name: str
    status: str  # "success" | "error"
    elapsed_ms: float = 0.0
    input_keys: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Process-global Object Store
# ---------------------------------------------------------------------------

class ObjectStore:
    """Thread-safe, in-memory object store for heavyweight Python objects."""

    _singleton: Optional["ObjectStore"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._objects: Dict[str, Any] = {}
        self._entries: Dict[str, ObjectEntry] = {}
        self._obj_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "ObjectStore":
        """Return the process-global singleton."""
        if cls._singleton is None:
            with cls._lock:
                if cls._singleton is None:
                    cls._singleton = cls()
        return cls._singleton

    def put(self, obj: Any, *, kind: str = "unknown", meta: Optional[Dict[str, Any]] = None) -> str:
        """Store *obj* and return a unique string ID."""
        obj_id = f"{kind}_{uuid.uuid4().hex[:12]}"
        entry = ObjectEntry(obj_id=obj_id, kind=kind, meta=meta or {})
        with self._obj_lock:
            self._objects[obj_id] = obj
            self._entries[obj_id] = entry
        logger.info("ObjectStore: stored %s (kind=%s)", obj_id, kind)
        return obj_id

    def get(self, obj_id: str) -> Any:
        """Retrieve the raw object by *obj_id*. Raises ``KeyError`` if not found."""
        with self._obj_lock:
            obj = self._objects.get(obj_id)
        if obj is None:
            raise KeyError(f"ObjectStore: ID '{obj_id}' not found. Available: {list(self._objects.keys())}")
        return obj

    def get_entry(self, obj_id: str) -> ObjectEntry:
        """Return the typed ``ObjectEntry`` for *obj_id*."""
        with self._obj_lock:
            entry = self._entries.get(obj_id)
        if entry is None:
            raise KeyError(f"ObjectStore: ID '{obj_id}' not found.")
        return entry

    def get_meta(self, obj_id: str) -> Dict[str, Any]:
        """Return the metadata dict attached to *obj_id*."""
        return self.get_entry(obj_id).meta

    def delete(self, obj_id: str) -> bool:
        """Remove *obj_id* from the store. Returns True if deleted."""
        with self._obj_lock:
            removed_obj = self._objects.pop(obj_id, None)
            self._entries.pop(obj_id, None)
        if removed_obj is not None:
            logger.info("ObjectStore: deleted %s", obj_id)
            return True
        return False

    def list_ids(self, kind: Optional[str] = None) -> List[str]:
        """Return all stored IDs, optionally filtered by *kind*."""
        with self._obj_lock:
            if kind:
                return [k for k, e in self._entries.items() if e.kind == kind]
            return list(self._entries.keys())

    def list_entries(self, kind: Optional[str] = None) -> List[ObjectEntry]:
        """Return typed entries, optionally filtered by *kind*."""
        with self._obj_lock:
            entries = list(self._entries.values())
        if kind:
            entries = [e for e in entries if e.kind == kind]
        return entries

    def stats(self) -> StoreStats:
        """Return a typed snapshot of store statistics."""
        with self._obj_lock:
            kinds: Dict[str, int] = {}
            for e in self._entries.values():
                kinds[e.kind] = kinds.get(e.kind, 0) + 1
            return StoreStats(total_objects=len(self._entries), kinds=kinds)

    def clear(self) -> int:
        """Remove all objects and return the count of items cleared."""
        with self._obj_lock:
            count = len(self._objects)
            self._objects.clear()
            self._entries.clear()
        logger.info("ObjectStore: cleared %d objects", count)
        return count


# ---------------------------------------------------------------------------
# Base Dynamic Adapter & Lifecycle Class
# ---------------------------------------------------------------------------

class BaseAdapter(ABC, Generic[T_in, T_out]):
    """Generic base class for typed adapters with lifecycle management."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize adapter resources."""
        self._is_initialized = True

    def cleanup(self) -> None:
        """Release adapter resources."""
        self._is_initialized = False

    def health_check(self) -> bool:
        """Verify health state of adapter."""
        return self._is_initialized

    @abstractmethod
    def adapt(self, input_data: T_in) -> T_out:
        """Core adaptation logic."""
        pass

    async def adapt_async(self, input_data: T_in) -> T_out:
        """Asynchronous adaptation execution wrapper."""
        return self.adapt(input_data)

    async def transform(self, input_data: T_in) -> T_out:
        """Standardized async transform pipeline stage."""
        if not self._is_initialized:
            self.initialize()
        return await self.adapt_async(input_data)

    async def execute(self, input_data: T_in) -> T_out:
        """Standardized async execution pipeline stage."""
        return await self.transform(input_data)

    def __enter__(self) -> "BaseAdapter[T_in, T_out]":
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()

    async def __aenter__(self) -> "BaseAdapter[T_in, T_out]":
        self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()


_BaseToolClass = BaseTool if BaseTool is not None else object


class BaseDynamicAdapter(_BaseToolClass, BaseAdapter[Dict[str, Any], Dict[str, Any]]):  # type: ignore[misc]
    """Base class for all intelligence-driven adapters discovering BaseTool."""

    @property
    def store(self) -> ObjectStore:
        """Convenience accessor to the global ObjectStore singleton."""
        return ObjectStore.instance()

    def adapt(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process(input_data)

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """The core logic of the adapter."""
        pass

    async def run(self, tool_input: str) -> Any:
        """Tool execution entry point parsing stringified JSON input."""
        start = time.monotonic()
        try:
            input_data = json.loads(tool_input)
            input_keys = list(input_data.keys())
            name_attr = getattr(self, "name", self.__class__.__name__)
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
            name_attr = getattr(self, "name", self.__class__.__name__)
            logger.error("Adapter '%s' failed to parse JSON input: %s", name_attr, exc)
            err_result = AdapterRunResult(
                adapter_name=name_attr, status="error", elapsed_ms=elapsed_ms,
            ).model_dump()
            if ToolResult is not None:
                return ToolResult(
                    output=f"Error: Invalid JSON input provided to {name_attr}. Details: {exc}",
                    metadata=err_result,
                )
            return {"error": str(exc), "metadata": err_result}
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            name_attr = getattr(self, "name", self.__class__.__name__)
            logger.exception("Adapter '%s' execution failed", name_attr)
            err_result = AdapterRunResult(
                adapter_name=name_attr, status="error", elapsed_ms=elapsed_ms,
            ).model_dump()
            if ToolResult is not None:
                return ToolResult(
                    output=f"Error during {name_attr} execution: {exc}",
                    metadata=err_result,
                )
            return {"error": str(exc), "metadata": err_result}


__all__ = [
    "BaseAdapterProtocol",
    "ObjectEntry",
    "StoreStats",
    "AdapterRunResult",
    "ObjectStore",
    "BaseAdapter",
    "BaseDynamicAdapter",
]
