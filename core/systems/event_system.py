"""
Event system for decoupled communication between modules.
Implements Observer pattern for maximum modularity with async & sync handler support.
"""
import logging
import asyncio
import inspect
from typing import Dict, List, Callable, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types."""
    TRAINING_STARTED = "training.started"
    TRAINING_STEP = "training.step"
    TRAINING_EPOCH = "training.epoch"
    TRAINING_FINISHED = "training.finished"
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_FINISHED = "evaluation.finished"
    CHECKPOINT_SAVED = "checkpoint.saved"
    CHECKPOINT_LOADED = "checkpoint.loaded"
    MODEL_LOADED = "model.loaded"
    MODEL_SAVED = "model.saved"
    ERROR_OCCURRED = "error.occurred"
    METRIC_LOGGED = "metric.logged"


@dataclass
class Event:
    """Event data structure."""
    event_type: Union[EventType, str]
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    @property
    def key(self) -> str:
        return self.event_type.value if isinstance(self.event_type, EventType) else str(self.event_type)


class EventEmitter:
    """
    Event emitter for publishing events.
    Supports synchronous and asynchronous handlers, thread-safety, and wildcards.
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._global_listeners: List[Callable] = []
        self._lock = threading.RLock()
    
    def _to_key(self, event_type: Union[EventType, str]) -> str:
        return event_type.value if isinstance(event_type, EventType) else str(event_type)
    
    def on(
        self,
        event_type: Union[EventType, str],
        handler: Callable[[Event], Any]
    ) -> None:
        """Register an event handler."""
        key = self._to_key(event_type)
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            if handler not in self._listeners[key]:
                self._listeners[key].append(handler)
            logger.debug(f"Handler registered for {key}")
    
    def once(
        self,
        event_type: Union[EventType, str],
        handler: Callable[[Event], Any]
    ) -> None:
        """Register a one-time event handler."""
        key = self._to_key(event_type)
        
        def wrapper(event: Event):
            try:
                if inspect.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(event))
                    except RuntimeError:
                        asyncio.run(handler(event))
                else:
                    handler(event)
            finally:
                self.off(key, wrapper)
        
        self.on(key, wrapper)
    
    def off(
        self,
        event_type: Union[EventType, str],
        handler: Optional[Callable] = None
    ) -> None:
        """Unregister an event handler."""
        key = self._to_key(event_type)
        with self._lock:
            if key in self._listeners:
                if handler:
                    self._listeners[key] = [h for h in self._listeners[key] if h != handler]
                else:
                    self._listeners[key].clear()
                logger.debug(f"Handler unregistered for {key}")
    
    def emit(
        self,
        event_type: Union[EventType, str],
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ) -> None:
        """Emit an event to all registered listeners."""
        key = self._to_key(event_type)
        event = Event(
            event_type=event_type,
            data=data or {},
            source=source
        )
        
        with self._lock:
            handlers = list(self._listeners.get(key, []))
            all_handlers = handlers + list(self._global_listeners)
        
        for handler in all_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(event))
                    except RuntimeError:
                        asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {key}: {e}", exc_info=True)
        
        logger.debug(f"Event emitted: {key} from {source}")
    
    def on_any(self, handler: Callable[[Event], Any]) -> None:
        """Register a handler for all events."""
        with self._lock:
            if handler not in self._global_listeners:
                self._global_listeners.append(handler)
    
    def remove_all_listeners(self, event_type: Optional[Union[EventType, str]] = None) -> None:
        """Remove all listeners for an event type or all events."""
        with self._lock:
            if event_type:
                key = self._to_key(event_type)
                self._listeners.pop(key, None)
            else:
                self._listeners.clear()
                self._global_listeners.clear()


# Global event emitter
_event_emitter = EventEmitter()


def get_event_emitter() -> EventEmitter:
    """Get the global event emitter."""
    return _event_emitter


def emit_event(
    event_type: Union[EventType, str],
    data: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None
) -> None:
    """Emit an event using the global emitter."""
    _event_emitter.emit(event_type, data, source)


def on_event(
    event_type: Union[EventType, str],
    handler: Callable[[Event], Any]
) -> None:
    """Register an event handler."""
    _event_emitter.on(event_type, handler)



