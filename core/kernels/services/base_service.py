"""
Base Service Interface for TruthGPT Kernel

Defines the contract that all kernel services must implement.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

try:
    from ...systems.event_system import EventEmitter, Event
except (ImportError, ValueError):
    try:
        from core.systems.event_system import EventEmitter, Event
    except ImportError:
        from optimization_core.core.systems.event_system import EventEmitter, Event


class ServiceState(Enum):
    """Service lifecycle states"""
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class BaseService(ABC):
    """Base class for all TruthGPT services"""
    
    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        self.kernel = kernel
        self.config = config or {}
        self.state = ServiceState.INITIALIZED
        self.logger = logging.getLogger(f"TruthGPT.{self.__class__.__name__}")
        
    @property
    def name(self) -> str:
        """Service name"""
        return self.__class__.__name__
    
    @property
    def is_running(self) -> bool:
        """Check if service is running"""
        return self.state == ServiceState.RUNNING
    
    async def start(self) -> None:
        """Start the service"""
        if self.state != ServiceState.INITIALIZED:
            raise RuntimeError(f"Service {self.name} cannot be started from state {self.state}")
        
        self.state = ServiceState.STARTING
        self.logger.info(f"Starting {self.name}...")
        
        try:
            await self._on_start()
            self.state = ServiceState.RUNNING
            await self._emit_event("service.started", {"service": self.name})
            self.logger.info(f"{self.name} started successfully")
            
        except Exception as e:
            self.state = ServiceState.ERROR
            await self._emit_event("service.error", {"service": self.name, "error": str(e)})
            self.logger.error(f"Failed to start {self.name}: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the service"""
        if self.state not in [ServiceState.RUNNING, ServiceState.ERROR]:
            return
        
        self.state = ServiceState.STOPPING
        self.logger.info(f"Stopping {self.name}...")
        
        try:
            await self._on_stop()
            self.state = ServiceState.STOPPED
            await self._emit_event("service.stopped", {"service": self.name})
            self.logger.info(f"{self.name} stopped")
            
        except Exception as e:
            self.state = ServiceState.ERROR
            await self._emit_event("service.error", {"service": self.name, "error": str(e)})
            self.logger.error(f"Error stopping {self.name}: {e}")
    
    async def restart(self) -> None:
        """Restart the service"""
        await self.stop()
        self.state = ServiceState.INITIALIZED
        await self.start()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "service": self.name,
            "state": self.state.value,
            "healthy": self.is_running,
            **await self._get_health_info()
        }
    
    @abstractmethod
    async def _on_start(self) -> None:
        """Service-specific startup logic"""
        pass
    
    @abstractmethod
    async def _on_stop(self) -> None:
        """Service-specific shutdown logic"""
        pass
    
    async def _get_health_info(self) -> Dict[str, Any]:
        """Get service-specific health information"""
        return {}
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event through the kernel's event system"""
        try:
            await self.kernel.event_emitter.emit(Event(event_type, data))
        except Exception as e:
            self.logger.error(f"Failed to emit event {event_type}: {e}")
