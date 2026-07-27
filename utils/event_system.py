try:
    from modules.infrastructure.event_system import (
        EventType,
        Event,
        EventEmitter,
        EventBus,
        get_event_bus,
        get_emitter
    )
except (ImportError, ValueError):
    from ..modules.infrastructure.event_system import (
        EventType,
        Event,
        EventEmitter,
        EventBus,
        get_event_bus,
        get_emitter
    )

__all__ = [
    'EventType',
    'Event',
    'EventEmitter',
    'EventBus',
    'get_event_bus',
    'get_emitter'
]
