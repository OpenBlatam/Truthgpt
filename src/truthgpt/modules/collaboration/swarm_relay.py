"""
🌐 SwarmRelay - Industrial Real-Time Collaboration Service (Refactored)
=====================================================================
Handles multi-user synchronization, shared state, and peer-to-peer 
communication via the Global Swarm Network using an Event-Driven architecture.
"""
import asyncio
import json
import logging
import uuid
import websockets
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

logger = logging.getLogger("collaboration.swarm_relay")

class SwarmEvent:
    """Standardized event types for the Swarm Network."""
    JOIN = "join"
    CHAT = "chat"
    CODE_UPDATE = "code_update"
    AGENT_UPDATE = "agent_update"
    STATE_SYNC = "state_sync"
    MEMORY_SYNC = "memory_sync"
    DISCOVERY = "discovery"

class SwarmRelay:
    def __init__(self, relay_url: str = "wss://socketsbay.com/wss/v2/1/demo/"):
        self.relay_url = relay_url
        self.client_id = f"node-{uuid.uuid4().hex[:8]}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._handlers: Dict[str, List[Callable]] = {}
        self.is_connected = False
        self.room_id = "global-swarm"
        self._listener_task: Optional[asyncio.Task] = None

    def on(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def connect(self):
        """Establish connection and start listener."""
        if self.is_connected:
            return

        try:
            self.websocket = await websockets.connect(self.relay_url)
            self.is_connected = True
            logger.info(f"Connected to Swarm Relay: {self.relay_url}")
            
            # Start background listener
            self._listener_task = asyncio.create_task(self._listen())
            
            # Broadcast join event
            await self.emit(SwarmEvent.JOIN, {"node_id": self.client_id})
        except Exception as e:
            self.is_connected = False
            logger.error(f"Connection failed: {e}")
            raise

    async def disconnect(self):
        self.is_connected = False
        if self._listener_task:
            self._listener_task.cancel()
        if self.websocket:
            await self.websocket.close()

    async def emit(self, event_type: str, data: Any):
        """Broadcast an event to the swarm."""
        if not self.is_connected or not self.websocket:
            return
        
        envelope = {
            "node_id": self.client_id,
            "room": self.room_id,
            "event": event_type,
            "data": data,
            "sent_at": datetime.now().isoformat()
        }
        try:
            await self.websocket.send(json.dumps(envelope))
        except Exception as e:
            logger.error(f"Emission error: {e}")
            self.is_connected = False

    async def _listen(self):
        """Internal listener loop."""
        try:
            async for message in self.websocket:
                try:
                    envelope = json.loads(message)
                    event_type = envelope.get("event")
                    data = envelope.get("data", {})
                    sender_id = envelope.get("node_id")
                    
                    if event_type in self._handlers:
                        for handler in self._handlers[event_type]:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(data, sender_id)
                            else:
                                handler(data, sender_id)
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"Listener error: {e}")
                    continue
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Relay listener terminated: {e}")
            self.is_connected = False
