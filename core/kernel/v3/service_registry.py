import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import time
from abc import ABC, abstractmethod


class ServiceStatus(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class ServiceMetadata:
    name: str
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    health_check_interval: float = 30.0
    max_restart_attempts: int = 3
    restart_delay: float = 5.0
    timeout: float = 30.0
    tags: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceInstance:
    metadata: ServiceMetadata
    service_object: Any
    status: ServiceStatus = ServiceStatus.STOPPED
    last_health_check: float = 0.0
    restart_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_error: Optional[str] = None


class ServiceInterface(ABC):
    """Base interface that all TruthGPT services must implement"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if service is healthy"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> ServiceMetadata:
        """Return service metadata"""
        pass


class ServiceRegistry:
    """Advanced Service Registry with dependency management and health monitoring"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInstance] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
    
    async def register_service(self, service: ServiceInterface) -> None:
        """Register a new service in the registry"""
        metadata = service.get_metadata()
        
        if metadata.name in self._services:
            raise ValueError(f"Service {metadata.name} is already registered")
        
        instance = ServiceInstance(
            metadata=metadata,
            service_object=service,
            status=ServiceStatus.STOPPED
        )
        
        self._services[metadata.name] = instance
        self._compute_startup_order()
        
        logger.info(f"Service {metadata.name} v{metadata.version} registered")
        await self._emit_event("service.registered", {"service_name": metadata.name})
    
    def _compute_startup_order(self) -> None:
        """Compute service startup order based on dependencies"""
        # Topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        startup_order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            if service_name in self._services:
                for dep in self._services[service_name].metadata.dependencies:
                    visit(dep)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            startup_order.append(service_name)
        
        for service_name in self._services.keys():
            if service_name not in visited:
                visit(service_name)
        
        self._startup_order = startup_order
        self._shutdown_order = startup_order[::-1]
        logger.debug(f"Computed startup order: {self._startup_order}")
    
    async def start_all_services(self) -> None:
        """Start all services in dependency order"""
        logger.info("Starting all services...")
        
        for service_name in self._startup_order:
            if service_name in self._services:
                await self._start_service(service_name)
        
        # Start health monitoring
        self._running = True
        self._health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        
        logger.info("All services started successfully")
    
    async def _start_service(self, service_name: str) -> None:
        """Start a specific service"""
        instance = self._services[service_name]
        
        if instance.status == ServiceStatus.RUNNING:
            return
        
        logger.info(f"Starting service: {service_name}")
        instance.status = ServiceStatus.STARTING
        
        try:
            # Check dependencies are running
            for dep_name in instance.metadata.dependencies:
                if dep_name not in self._services:
                    raise RuntimeError(f"Dependency {dep_name} is not registered")
                if self._services[dep_name].status != ServiceStatus.RUNNING:
                    raise RuntimeError(f"Dependency {dep_name} is not running")
            
            # Start the service with timeout
            await asyncio.wait_for(
                instance.service_object.start(),
                timeout=instance.metadata.timeout
            )
            
            # Verify it's healthy
            if await instance.service_object.health_check():
                instance.status = ServiceStatus.RUNNING
                instance.last_health_check = time.time()
                logger.info(f"Service {service_name} started successfully")
                await self._emit_event("service.started", {"service_name": service_name})
            else:
                raise RuntimeError(f"Service {service_name} failed health check after start")
                
        except Exception as e:
            instance.status = ServiceStatus.FAILED
            instance.last_error = str(e)
            logger.error(f"Failed to start service {service_name}: {e}")
            await self._emit_event("service.failed", {"service_name": service_name, "error": str(e)})
            raise
    
    async def stop_all_services(self) -> None:
        """Stop all services in reverse dependency order"""
        logger.info("Stopping all services...")
        
        # Stop health monitoring
        self._running = False
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop services
        for service_name in self._shutdown_order:
            if service_name in self._services:
                await self._stop_service(service_name)
        
        logger.info("All services stopped")
    
    async def _stop_service(self, service_name: str) -> None:
        """Stop a specific service"""
        instance = self._services[service_name]
        
        if instance.status in [ServiceStatus.STOPPED, ServiceStatus.STOPPING]:
            return
        
        logger.info(f"Stopping service: {service_name}")
        instance.status = ServiceStatus.STOPPING
        
        try:
            await asyncio.wait_for(
                instance.service_object.stop(),
                timeout=instance.metadata.timeout
            )
            instance.status = ServiceStatus.STOPPED
            logger.info(f"Service {service_name} stopped successfully")
            await self._emit_event("service.stopped", {"service_name": service_name})
            
        except Exception as e:
            instance.status = ServiceStatus.FAILED
            instance.last_error = str(e)
            logger.error(f"Failed to stop service {service_name}: {e}")
    
    async def _health_monitor_loop(self) -> None:
        """Continuous health monitoring of all services"""
        while self._running:
            try:
                for service_name, instance in self._services.items():
                    if instance.status == ServiceStatus.RUNNING:
                        await self._check_service_health(service_name)
                
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _check_service_health(self, service_name: str) -> None:
        """Check health of a specific service"""
        instance = self._services[service_name]
        current_time = time.time()
        
        # Skip if recently checked
        if current_time - instance.last_health_check < instance.metadata.health_check_interval:
            return
        
        try:
            is_healthy = await asyncio.wait_for(
                instance.service_object.health_check(),
                timeout=10.0
            )
            
            if is_healthy:
                instance.last_health_check = current_time
            else:
                logger.warning(f"Service {service_name} failed health check")
                await self._handle_unhealthy_service(service_name)
                
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            await self._handle_unhealthy_service(service_name)
    
    async def _handle_unhealthy_service(self, service_name: str) -> None:
        """Handle an unhealthy service with restart logic"""
        instance = self._services[service_name]
        
        if instance.restart_count >= instance.metadata.max_restart_attempts:
            logger.error(f"Service {service_name} exceeded max restart attempts")
            instance.status = ServiceStatus.FAILED
            await self._emit_event("service.failed", {"service_name": service_name})
            return
        
        logger.info(f"Attempting to restart service {service_name}")
        instance.status = ServiceStatus.RECOVERING
        instance.restart_count += 1
        
        try:
            # Stop and restart
            await self._stop_service(service_name)
            await asyncio.sleep(instance.metadata.restart_delay)
            await self._start_service(service_name)
            
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            instance.status = ServiceStatus.FAILED
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get the current status of a service"""
        if service_name in self._services:
            return self._services[service_name].status
        return None
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services with their status"""
        return {
            name: {
                "status": instance.status.value,
                "version": instance.metadata.version,
                "restart_count": instance.restart_count,
                "last_health_check": instance.last_health_check,
                "dependencies": instance.metadata.dependencies,
                "last_error": instance.last_error
            }
            for name, instance in self._services.items()
        }
    
    def subscribe_to_events(self, event_type: str, handler: Callable) -> None:
        """Subscribe to service lifecycle events"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit a service lifecycle event"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type}: {e}")