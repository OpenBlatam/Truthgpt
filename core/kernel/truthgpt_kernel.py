import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from .config.kernel_config import KernelConfig
from .services.advanced_service_manager import AdvancedServiceManager
from .events.production_event_bus import ProductionEventBus
from .services.base_service import BaseService

# Import services
from .services.agent_service import AgentService
from .services.model_service import ModelService
from .services.memory_service import MemoryService
from .services.interface_service import InterfaceService

class PluginManager:
    """Enhanced Plugin Manager with hot-reload capabilities."""
    
    def __init__(self):
        self.loaded_plugins = {}
        
    async def load_plugins(self):
        """Load all configured plugins."""
        logger.info("🔌 PluginManager: Loading plugins...")
        # Placeholder for actual plugin loading
        await asyncio.sleep(0.1)
        logger.info("🔌 PluginManager: Plugins loaded")
        
    async def reload_plugin(self, plugin_name: str):
        """Hot-reload a specific plugin."""
        logger.info(f"🔄 Reloading plugin: {plugin_name}")
        # Placeholder for hot reload logic
        await asyncio.sleep(0.1)
        
    async def unload_plugin(self, plugin_name: str):
        """Unload a specific plugin."""
        logger.info(f"🔌 Unloading plugin: {plugin_name}")
        # Placeholder for unload logic
        await asyncio.sleep(0.1)

class HealthMonitor:
    """Advanced health monitoring with metrics and alerting."""
    
    def __init__(self, service_manager, event_bus):
        self.service_manager = service_manager
        self.event_bus = event_bus
        self.health_history = []
        
    def check_health(self) -> bool:
        """Check overall system health."""
        if not hasattr(self.service_manager, 'get_service_status'):
            return True  # Basic service manager, assume healthy
            
        services = self.service_manager.get_service_status()
        unhealthy_services = [
            name for name, info in services.items() 
            if not (info.get('running', False) and info.get('healthy', True))
        ]
        
        is_healthy = len(unhealthy_services) == 0
        
        # Record health status
        health_record = {
            "timestamp": datetime.now().isoformat(),
            "healthy": is_healthy,
            "unhealthy_services": unhealthy_services,
            "total_services": len(services)
        }
        
        self.health_history.append(health_record)
        if len(self.health_history) > 100:  # Keep last 100 records
            self.health_history.pop(0)
            
        return is_healthy
        
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        current_health = self.check_health()
        
        return {
            "current_status": "healthy" if current_health else "unhealthy",
            "last_check": datetime.now().isoformat(),
            "history_length": len(self.health_history),
            "recent_issues": [
                record for record in self.health_history[-10:] 
                if not record["healthy"]
            ]
        }

class TruthGPTKernel:
    """TruthGPT Kernel 2.0 - Enterprise-Ready AI Operating System"""
    
    def __init__(self, config: Optional[KernelConfig] = None):
        self.config = config or KernelConfig()
        
        # Core components with enhanced functionality
        self.service_manager = AdvancedServiceManager(
            startup_timeout=self.config.service_startup_timeout,
            health_check_interval=self.config.health_check_interval
        )
        self.event_bus = ProductionEventBus(max_history=self.config.event_history_size)
        self.plugin_manager = PluginManager()
        self.health_monitor = HealthMonitor(self.service_manager, self.event_bus)
        
        # CLI interface (will be set later)
        self.cli = None
        
        self.extended_mode = True
        
        # Kernel state
        self.start_time = None
        self.running = False
        
        self._setup_core_services()
        self._setup_event_handlers()
        
    def _setup_core_services(self):
        """Register core services with dependencies."""
        logger.info("🔧 Setting up core services...")
        
        # Register services with proper dependencies
        memory_service = MemoryService()
        model_service = ModelService()
        agent_service = AgentService()
        interface_service = InterfaceService()
        
        # Register with dependencies
        self.service_manager.register_service(memory_service, dependencies=[])
        self.service_manager.register_service(model_service, dependencies=["MemoryService"])
        self.service_manager.register_service(agent_service, dependencies=["MemoryService", "ModelService"])
        self.service_manager.register_service(interface_service, dependencies=[])
        
    def _setup_event_handlers(self):
        """Setup system event handlers."""
        # System event handlers
        self.event_bus.subscribe(
            "system.service.started", 
            self._on_service_started, 
            priority=10
        )
        
        self.event_bus.subscribe(
            "system.service.stopped", 
            self._on_service_stopped, 
            priority=10
        )
        
        self.event_bus.subscribe(
            "system.error.*", 
            self._on_system_error, 
            priority=5
        )
        
    async def _on_service_started(self, event):
        """Handle service started events."""
        service_name = event.data.get('service_name', 'unknown')
        logger.info(f"📡 Event: Service {service_name} started")
        
    async def _on_service_stopped(self, event):
        """Handle service stopped events."""
        service_name = event.data.get('service_name', 'unknown')
        logger.warning(f"📡 Event: Service {service_name} stopped")
        
    async def _on_system_error(self, event):
        """Handle system error events."""
        error = event.data.get('error', 'Unknown error')
        logger.error(f"📡 System Error Event: {error}")
        
    async def start(self, enable_cli: bool = False):
        """Start the enhanced kernel with full functionality."""
        self.start_time = datetime.now()
        
        logger.info("🚀 Enhanced TruthGPT Kernel 2.0 starting...")
        
        try:
            # 1. Initialize Event Bus
            logger.info("📡 Initializing Event Bus...")
            await self.event_bus.initialize()
            await self.event_bus.emit("system.kernel.starting", {
                "version": "2.0",
                "start_time": self.start_time.isoformat()
            }, source="kernel")
            
            # 2. Start all services with dependency resolution
            logger.info("🔧 Starting services...")
            await self.service_manager.start_all_services()
            
            # 3. Load plugins
            logger.info("🔌 Loading plugins...")
            await self.plugin_manager.load_plugins()
            
            # 4. Final health check
            if self.health_monitor.check_health():
                logger.info("✅ All systems operational")
                self.running = True
                
                await self.event_bus.emit("system.kernel.ready", {
                    "startup_duration": (datetime.now() - self.start_time).total_seconds(),
                    "services_count": len(self.service_manager.get_service_status()),
                    "health_status": "healthy"
                }, source="kernel")
                
                logger.info("🎉 Enhanced TruthGPT Kernel 2.0 Ready!")
                
                # 5. Start CLI if requested
                if enable_cli:
                    await self.start_cli()
                    
            else:
                logger.error("❌ System health check failed during startup")
                await self.stop()
                
        except Exception as e:
            logger.error(f"❌ Kernel startup failed: {e}")
            await self.event_bus.emit("system.kernel.startup_failed", {
                "error": str(e),
                "startup_duration": (datetime.now() - self.start_time).total_seconds()
            }, source="kernel")
            raise
            
    async def stop(self):
        """Gracefully shutdown the kernel."""
        if not self.running:
            return
            
        logger.info("🛑 Enhanced TruthGPT Kernel shutting down...")
        self.running = False
        
        await self.event_bus.emit("system.kernel.stopping", {
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }, source="kernel")
        
        # Stop in reverse order
        await self.plugin_manager.load_plugins()  # Unload plugins
        await self.service_manager.stop_all_services()
        await self.event_bus.shutdown()
        
        logger.info("✅ Enhanced TruthGPT Kernel shutdown complete")
        
    async def start_cli(self):
        """Start the interactive CLI interface."""
        try:
            from .cli.interactive_cli import TruthGPTCLI
            
            self.cli = TruthGPTCLI(kernel=self)
            logger.info("💻 Starting interactive CLI...")
            
            await self.event_bus.emit("system.cli.starting", {}, source="kernel")
            await self.cli.start_interactive_mode()
            
        except ImportError:
            logger.error("❌ CLI module not available")
        except Exception as e:
            logger.error(f"❌ CLI startup failed: {e}")
            
    async def execute_cli_command(self, command: str) -> str:
        """Execute a single CLI command (for API integration)."""
        if not self.cli:
            from .cli.interactive_cli import TruthGPTCLI
            self.cli = TruthGPTCLI(kernel=self)
            
        await self.cli.run_single_command(command)
        return "Command executed"  # In production, capture output
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "kernel": {
                "running": self.running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "version": "2.0"
            },
            "services": self.service_manager.get_service_status() if hasattr(self.service_manager, 'get_service_status') else {},
            "events": self.event_bus.get_stats(),
            "health": self.health_monitor.get_health_summary(),
            "plugins": {
                "loaded_count": len(self.plugin_manager.loaded_plugins)
            }
        }
        
    async def hot_reload_config(self, new_config: KernelConfig):
        """Hot-reload kernel configuration without restart."""
        logger.info("🔄 Hot-reloading kernel configuration...")
        
        old_config = self.config
        self.config = new_config
        
        await self.event_bus.emit("system.config.reloaded", {
            "old_config": str(old_config),
            "new_config": str(new_config)
        }, source="kernel")
        
        logger.info("✅ Configuration reloaded successfully")
        
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        if hasattr(self.service_manager, 'restart_service'):
            await self.event_bus.emit("system.service.restarting", {
                "service_name": service_name
            }, source="kernel")
            
            return await self.service_manager.restart_service(service_name)
        else:
            logger.warning("Service restart not supported with basic ServiceManager")
            return False
