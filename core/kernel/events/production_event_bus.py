import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from loguru import logger
import json
import uuid

@dataclass
class Event:
    """Represents an event in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
        
    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.type}: {self.source or 'unknown'}"

class EventHandler:
    """Wrapper for event handler functions with metadata."""
    def __init__(self, handler: Callable, priority: int = 0, once: bool = False):
        self.handler = handler
        self.priority = priority
        self.once = once
        self.call_count = 0
        
class ProductionEventBus:
    """Production-ready event bus with pub/sub, history, and async support."""
    
    def __init__(self, max_history: int = 1000):
        self.subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = max_history
        self.stats = {
            "events_emitted": 0,
            "handlers_executed": 0,
            "errors": 0
        }
        self._running = False
        
    async def initialize(self):
        """Initialize the event bus."""
        self._running = True
        logger.info("🔧 Event Bus initialized")
        await self.emit("system.eventbus.initialized", {"timestamp": datetime.now().isoformat()})
        
    async def shutdown(self):
        """Shutdown the event bus gracefully."""
        self._running = False
        await self.emit("system.eventbus.shutdown", {"timestamp": datetime.now().isoformat()})
        logger.info("🔧 Event Bus shut down")
        
    def subscribe(self, event_type: str, handler: Callable, priority: int = 0, once: bool = False):
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to listen for (supports wildcards with *)
            handler: Async function to call when event occurs
            priority: Handler priority (higher numbers execute first)
            once: If True, handler is removed after first execution
        """
        event_handler = EventHandler(handler, priority, once)
        self.subscribers[event_type].append(event_handler)
        
        # Sort by priority (highest first)
        self.subscribers[event_type].sort(key=lambda h: h.priority, reverse=True)
        
        logger.debug(f"Subscribed to '{event_type}' (priority: {priority}, once: {once})")
        
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from events."""
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                h for h in self.subscribers[event_type] 
                if h.handler != handler
            ]
            logger.debug(f"Unsubscribed from '{event_type}'")
            
    async def emit(self, event_type: str, data: Dict[str, Any] = None, source: str = None) -> Event:
        """Emit an event to all subscribers.
        
        Args:
            event_type: Type of event
            data: Event payload
            source: Source of the event
            
        Returns:
            The created Event object
        """
        if not self._running:
            logger.warning(f"Event bus not running, dropping event: {event_type}")
            return None
            
        # Create event
        event = Event(
            type=event_type,
            data=data or {},
            source=source
        )
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
            
        self.stats["events_emitted"] += 1
        
        logger.debug(f"Emitting event: {event_type} from {source or 'unknown'}")
        
        # Find matching handlers
        matching_handlers = []
        
        # Exact match
        if event_type in self.subscribers:
            matching_handlers.extend(self.subscribers[event_type])
            
        # Wildcard matches
        for pattern in self.subscribers:
            if '*' in pattern and self._matches_pattern(event_type, pattern):
                matching_handlers.extend(self.subscribers[pattern])
                
        # Sort by priority
        matching_handlers.sort(key=lambda h: h.priority, reverse=True)
        
        # Execute handlers
        for handler in matching_handlers:
            try:
                await self._execute_handler(handler, event)
                
                # Remove 'once' handlers
                if handler.once:
                    for event_pattern, handlers in self.subscribers.items():
                        if handler in handlers:
                            handlers.remove(handler)
                            break
                            
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Error in event handler for {event_type}: {e}")
                
        return event
        
    async def emit_and_wait(self, event_type: str, data: Dict[str, Any] = None, 
                           source: str = None, timeout: float = 5.0) -> List[Any]:
        """Emit an event and wait for all handlers to complete, collecting results."""
        event = await self.emit(event_type, data, source)
        
        # This is a simplified version - in production you'd want to track 
        # handler execution and collect results
        await asyncio.sleep(0.1)  # Give handlers time to execute
        
        return []  # Placeholder for handler results
        
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches a wildcard pattern."""
        import fnmatch
        return fnmatch.fnmatch(event_type, pattern)
        
    async def _execute_handler(self, handler: EventHandler, event: Event):
        """Execute a single event handler safely."""
        try:
            if asyncio.iscoroutinefunction(handler.handler):
                await handler.handler(event)
            else:
                # Run sync handler in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, handler.handler, event
                )
                
            handler.call_count += 1
            self.stats["handlers_executed"] += 1
            
        except Exception as e:
            logger.error(f"Handler execution failed: {e}")
            raise
            
    def get_subscribers_count(self, event_type: str = None) -> int:
        """Get number of subscribers for an event type or total."""
        if event_type:
            return len(self.subscribers.get(event_type, []))
        else:
            return sum(len(handlers) for handlers in self.subscribers.values())
            
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self.stats,
            "subscribers_count": self.get_subscribers_count(),
            "event_types": len(self.subscribers),
            "history_size": len(self.event_history),
            "running": self._running
        }
        
    def get_recent_events(self, count: int = 10, event_type: str = None) -> List[Event]:
        """Get recent events, optionally filtered by type."""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type or self._matches_pattern(e.type, event_type)]
            
        return events[-count:] if events else []
        
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
        logger.info("Event history cleared")
        
    def export_events(self, filename: str, event_type: str = None):
        """Export events to JSON file."""
        events_to_export = self.event_history
        
        if event_type:
            events_to_export = [e for e in events_to_export if e.type == event_type]
            
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_events": len(events_to_export),
            "event_type_filter": event_type,
            "events": [event.to_dict() for event in events_to_export]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Exported {len(events_to_export)} events to {filename}")
