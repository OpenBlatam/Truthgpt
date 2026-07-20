import asyncio
from typing import Dict, List, Optional, Set
from collections import defaultdict, deque
from loguru import logger
import time

from .base_service import BaseService

class DependencyError(Exception):
    """Raised when there's a circular dependency or missing dependency."""
    pass

class ServiceStartupError(Exception):
    """Raised when a service fails to start."""
    pass

class AdvancedServiceManager:
    """Advanced Service Manager with dependency resolution, health monitoring, and recovery."""
    
    def __init__(self, startup_timeout: float = 30.0, health_check_interval: float = 60.0):
        self.services: Dict[str, BaseService] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.startup_timeout = startup_timeout
        self.health_check_interval = health_check_interval
        self.startup_times: Dict[str, float] = {}
        self.restart_counts: Dict[str, int] = defaultdict(int)
        self._health_check_task: Optional[asyncio.Task] = None
        
    def register_service(self, service: BaseService, dependencies: List[str] = None):
        """Register a service with optional dependencies."""
        if service.name in self.services:
            logger.warning(f"Service {service.name} is already registered. Replacing...")
            
        self.services[service.name] = service
        
        if dependencies:
            self.dependencies[service.name] = set(dependencies)
            # Validate dependencies exist
            for dep in dependencies:
                if dep not in self.services:
                    logger.warning(f"Service {service.name} depends on {dep} which is not registered yet.")
                    
        logger.info(f"Registered service: {service.name} with dependencies: {dependencies or []}")
        
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get a registered service by name."""
        return self.services.get(service_name)
        
    def _resolve_startup_order(self) -> List[str]:
        """Resolve service startup order using topological sort."""
        # Kahn's algorithm for topological sorting
        in_degree = {name: 0 for name in self.services}
        
        # Calculate in-degrees
        for service_name, deps in self.dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[service_name] += 1
                else:
                    raise DependencyError(f"Service {service_name} depends on unknown service: {dep}")
                    
        # Find services with no dependencies
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove current service from dependencies of others
            for service_name, deps in self.dependencies.items():
                if current in deps:
                    in_degree[service_name] -= 1
                    if in_degree[service_name] == 0:
                        queue.append(service_name)
                        
        # Check for circular dependencies
        if len(result) != len(self.services):
            remaining = set(self.services.keys()) - set(result)
            raise DependencyError(f"Circular dependency detected involving: {remaining}")
            
        return result
        
    async def start_service(self, service_name: str) -> bool:
        """Start a specific service with timeout and error handling."""
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found")
            return False
            
        service = self.services[service_name]
        
        if service.is_running:
            logger.info(f"Service {service_name} is already running")
            return True
            
        logger.info(f"Starting service: {service_name}")
        start_time = time.time()
        
        try:
            await asyncio.wait_for(service.start(), timeout=self.startup_timeout)
            duration = time.time() - start_time
            self.startup_times[service_name] = duration
            logger.info(f"✅ Service {service_name} started successfully in {duration:.2f}s")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Service {service_name} startup timed out after {self.startup_timeout}s")
            return False
            
        except Exception as e:
            logger.error(f"❌ Service {service_name} failed to start: {e}")
            return False
            
    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service gracefully."""
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found")
            return False
            
        service = self.services[service_name]
        
        if not service.is_running:
            logger.info(f"Service {service_name} is already stopped")
            return True
            
        logger.info(f"Stopping service: {service_name}")
        
        try:
            await asyncio.wait_for(service.stop(), timeout=10.0)
            logger.info(f"✅ Service {service_name} stopped successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Service {service_name} shutdown timed out")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error stopping service {service_name}: {e}")
            return False
            
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        logger.info(f"Restarting service: {service_name}")
        self.restart_counts[service_name] += 1
        
        success = await self.stop_service(service_name)
        if not success:
            logger.error(f"Failed to stop service {service_name} for restart")
            return False
            
        # Wait a moment before restarting
        await asyncio.sleep(1.0)
        
        return await self.start_service(service_name)
        
    async def start_all_services(self):
        """Start all services in dependency order with parallel execution where possible."""
        if not self.services:
            logger.info("No services to start")
            return
            
        logger.info(f"🚀 Starting {len(self.services)} services...")
        
        try:
            startup_order = self._resolve_startup_order()
            logger.info(f"Service startup order: {startup_order}")
            
            # Group services that can start in parallel
            level_groups = self._get_parallel_startup_groups(startup_order)
            
            total_start_time = time.time()
            
            for level, service_group in enumerate(level_groups):
                if len(service_group) > 1:
                    logger.info(f"Starting level {level} services in parallel: {service_group}")
                    # Start services in parallel
                    tasks = [self.start_service(name) for name in service_group]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Check if any failed
                    failed = []
                    for i, result in enumerate(results):
                        if isinstance(result, Exception) or not result:
                            failed.append(service_group[i])
                    
                    if failed:
                        raise ServiceStartupError(f"Failed to start services: {failed}")
                else:
                    # Single service
                    service_name = service_group[0]
                    success = await self.start_service(service_name)
                    if not success:
                        raise ServiceStartupError(f"Failed to start service: {service_name}")
                        
            total_duration = time.time() - total_start_time
            logger.info(f"✅ All services started successfully in {total_duration:.2f}s")
            
            # Start health monitoring
            self._start_health_monitoring()
            
        except DependencyError as e:
            logger.error(f"Dependency error: {e}")
            raise
        except ServiceStartupError as e:
            logger.error(f"Service startup error: {e}")
            raise
            
    def _get_parallel_startup_groups(self, startup_order: List[str]) -> List[List[str]]:
        """Group services that can start in parallel (no dependencies between them)."""
        groups = []
        remaining = set(startup_order)
        started = set()
        
        while remaining:
            # Find services that can start now (all dependencies satisfied)
            can_start = []
            for service_name in remaining:
                deps = self.dependencies.get(service_name, set())
                if deps.issubset(started):
                    can_start.append(service_name)
                    
            if not can_start:
                # This shouldn't happen if topological sort worked
                raise DependencyError(f"Cannot find startable services from: {remaining}")
                
            groups.append(can_start)
            remaining -= set(can_start)
            started.update(can_start)
            
        return groups
        
    async def stop_all_services(self):
        """Stop all services in reverse dependency order."""
        if not self.services:
            logger.info("No services to stop")
            return
            
        # Stop health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            
        logger.info("🛑 Shutting down all services...")
        
        try:
            startup_order = self._resolve_startup_order()
            # Reverse order for shutdown
            shutdown_order = list(reversed(startup_order))
            
            for service_name in shutdown_order:
                await self.stop_service(service_name)
                
            logger.info("✅ All services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")
            
    def get_service_status(self) -> Dict[str, dict]:
        """Get comprehensive status of all services."""
        status = {}
        
        for name, service in self.services.items():
            status[name] = {
                "running": service.is_running,
                "healthy": service.check_health(),
                "startup_time": self.startup_times.get(name),
                "restart_count": self.restart_counts.get(name, 0),
                "dependencies": list(self.dependencies.get(name, set()))
            }
            
        return status
        
    def _start_health_monitoring(self):
        """Start background health monitoring task."""
        if self._health_check_task:
            self._health_check_task.cancel()
            
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        
    async def _health_monitor_loop(self):
        """Background task to monitor service health and restart if needed."""
        logger.info(f"🏥 Health monitoring started (interval: {self.health_check_interval}s)")
        
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                unhealthy_services = []
                for name, service in self.services.items():
                    if service.is_running and not service.check_health():
                        unhealthy_services.append(name)
                        
                if unhealthy_services:
                    logger.warning(f"Unhealthy services detected: {unhealthy_services}")
                    
                    for service_name in unhealthy_services:
                        restart_count = self.restart_counts.get(service_name, 0)
                        if restart_count < 3:  # Max 3 restart attempts
                            logger.info(f"Auto-restarting unhealthy service: {service_name}")
                            asyncio.create_task(self.restart_service(service_name))
                        else:
                            logger.error(f"Service {service_name} exceeded max restart attempts")
                            
            except asyncio.CancelledError:
                logger.info("Health monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
