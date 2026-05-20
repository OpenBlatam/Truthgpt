"""
Refactored PiMoE Base Classes and Interfaces
Clean architecture with separation of concerns, dependency injection, and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
from contextlib import contextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import asyncio

# Type definitions
T = TypeVar('T')
RequestData = Dict[str, Any]
ResponseData = Dict[str, Any]
ConfigData = Dict[str, Any]

class ProductionMode(Enum):
    """Production deployment modes."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"
    COST_OPTIMIZED = "cost_optimized"

class LogLevel(Enum):
    """Logging levels for production."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Protocols (Interfaces)
class LoggerProtocol(Protocol):
    """Logger interface."""
    def log_info(self, message: str, **kwargs) -> None: ...
    def log_warning(self, message: str, **kwargs) -> None: ...
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None: ...
    def log_metrics(self, metrics: Dict[str, Any]) -> None: ...

class MonitorProtocol(Protocol):
    """Monitor interface."""
    def record_request(self, success: bool = True) -> None: ...
    def get_health_status(self) -> Dict[str, Any]: ...

class ErrorHandlerProtocol(Protocol):
    """Error handler interface."""
    def handle_error(self, error: Exception, context: str = "") -> bool: ...
    def should_circuit_break(self) -> bool: ...

class RequestQueueProtocol(Protocol):
    """Request queue interface."""
    def submit_request(self, request_data: RequestData, callback: Any) -> str: ...
    def get_queue_stats(self) -> Dict[str, Any]: ...

class PiMoEProcessorProtocol(Protocol):
    """PiMoE processor interface."""
    def process_request(self, request_data: RequestData) -> ResponseData: ...
    def get_system_stats(self) -> Dict[str, Any]: ...
    def health_check(self) -> Dict[str, Any]: ...

# Base Configuration Classes
@dataclass
class BaseConfig:
    """Base configuration class."""
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def update(self, **kwargs) -> None:
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

@dataclass
class SystemConfig(BaseConfig):
    """System configuration."""
    hidden_size: int = 512
    num_experts: int = 8
    max_batch_size: int = 32
    max_sequence_length: int = 2048

@dataclass
class ProductionConfig(BaseConfig):
    """Production configuration."""
    # System configuration
    system_config: SystemConfig = field(default_factory=SystemConfig)
    
    # Production settings
    production_mode: ProductionMode = ProductionMode.PRODUCTION
    log_level: LogLevel = LogLevel.INFO
    enable_monitoring: bool = True
    enable_metrics: bool = True
    enable_health_checks: bool = True
    
    # Performance settings
    enable_quantization: bool = True
    enable_pruning: bool = True
    enable_distillation: bool = False
    mixed_precision: bool = True
    
    # Scalability settings
    max_concurrent_requests: int = 100
    request_timeout: float = 30.0
    memory_threshold_mb: float = 8000.0
    cpu_threshold_percent: float = 80.0
    
    # Monitoring settings
    metrics_interval: float = 1.0
    health_check_interval: float = 5.0
    log_interval: float = 10.0
    
    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 10
    
    # Deployment settings
    model_version: str = "1.0.0"
    deployment_id: str = "pimoe-prod-001"
    environment: str = "production"

# Base Service Classes
class BaseService(ABC):
    """Base service class with common functionality."""
    
    def __init__(self, config: BaseConfig, logger: Optional[LoggerProtocol] = None):
        self.config = config
        self.logger = logger or self._create_default_logger()
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service."""
        pass
    
    def _create_default_logger(self) -> LoggerProtocol:
        """Create default logger implementation."""
        return DefaultLogger()
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized

class DefaultLogger:
    """Default logger implementation."""
    
    def __init__(self):
        self.logger = logging.getLogger('pimoe_default')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_info(self, message: str, **kwargs) -> None:
        self.logger.info(f"{message} | {kwargs}")
    
    def log_warning(self, message: str, **kwargs) -> None:
        self.logger.warning(f"{message} | {kwargs}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        if exception:
            self.logger.error(f"{message} | {kwargs}", exc_info=exception)
        else:
            self.logger.error(f"{message} | {kwargs}")
    
    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        self.logger.info(f"Metrics: {metrics}")

# Service Factory
class ServiceFactory:
    """Factory for creating services with dependency injection."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, service_class: type, singleton: bool = False) -> None:
        """Register a service class."""
        self._services[name] = (service_class, singleton)
    
    def create(self, name: str, *args, **kwargs) -> Any:
        """Create a service instance."""
        if name in self._singletons:
            return self._singletons[name]
        
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        
        service_class, is_singleton = self._services[name]
        instance = service_class(*args, **kwargs)
        
        if is_singleton:
            self._singletons[name] = instance
        
        return instance
    
    def get(self, name: str) -> Any:
        """Get a registered service instance."""
        if name not in self._singletons:
            raise ValueError(f"Service '{name}' not found")
        return self._singletons[name]

# Dependency Injection Container
class DIContainer:
    """Dependency injection container."""
    
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register_instance(self, interface: str, instance: Any) -> None:
        """Register a concrete instance."""
        self._dependencies[interface] = instance
    
    def register_factory(self, interface: str, factory: callable) -> None:
        """Register a factory function."""
        self._factories[interface] = factory
    
    def get(self, interface: str) -> Any:
        """Get dependency by interface."""
        if interface in self._dependencies:
            return self._dependencies[interface]
        
        if interface in self._factories:
            return self._factories[interface]()
        
        raise ValueError(f"Dependency '{interface}' not found")
    
    def resolve(self, interface: str) -> Any:
        """Resolve dependency with type hints."""
        return self.get(interface)

# Configuration Manager
class ConfigManager:
    """Configuration manager with validation and updates."""
    
    def __init__(self, config: BaseConfig):
        self.config = config
        self._validators: Dict[str, callable] = {}
        self._observers: List[callable] = []
    
    def register_validator(self, field: str, validator: callable) -> None:
        """Register a field validator."""
        self._validators[field] = validator
    
    def register_observer(self, observer: callable) -> None:
        """Register a configuration change observer."""
        self._observers.append(observer)
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with validation."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                # Validate if validator exists
                if key in self._validators:
                    if not self._validators[key](value):
                        raise ValueError(f"Invalid value for {key}: {value}")
                
                # Update value
                setattr(self.config, key, value)
                
                # Notify observers
                for observer in self._observers:
                    observer(key, value)
    
    def get_config(self) -> BaseConfig:
        """Get current configuration."""
        return self.config

# Event System
class Event:
    """Event class for event-driven architecture."""
    
    def __init__(self, name: str, data: Dict[str, Any] = None):
        self.name = name
        self.data = data or {}
        self.timestamp = time.time()
        self.cancelled = False
    
    def cancel(self) -> None:
        """Cancel the event."""
        self.cancelled = True

class EventBus:
    """Event bus for decoupled communication."""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = {}
        self._middleware: List[callable] = []
    
    def subscribe(self, event_name: str, handler: callable) -> None:
        """Subscribe to an event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: callable) -> None:
        """Unsubscribe from an event."""
        if event_name in self._handlers:
            self._handlers[event_name].remove(handler)
    
    def add_middleware(self, middleware: callable) -> None:
        """Add event middleware."""
        self._middleware.append(middleware)
    
    def publish(self, event: Event) -> None:
        """Publish an event."""
        if event.cancelled:
            return
        
        # Apply middleware
        for middleware in self._middleware:
            middleware(event)
            if event.cancelled:
                return
        
        # Call handlers
        if event.name in self._handlers:
            for handler in self._handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    print(f"Error in event handler: {e}")

# Resource Manager
class ResourceManager:
    """Resource manager for system resources."""
    
    def __init__(self, config: BaseConfig):
        self.config = config
        self._resources: Dict[str, Any] = {}
        self._cleanup_handlers: List[callable] = []
    
    def register_resource(self, name: str, resource: Any, cleanup: callable = None) -> None:
        """Register a resource."""
        self._resources[name] = resource
        if cleanup:
            self._cleanup_handlers.append(cleanup)
    
    def get_resource(self, name: str) -> Any:
        """Get a resource."""
        if name not in self._resources:
            raise ValueError(f"Resource '{name}' not found")
        return self._resources[name]
    
    def cleanup_all(self) -> None:
        """Cleanup all resources."""
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                print(f"Error during cleanup: {e}")
    
    @contextmanager
    def managed_resource(self, name: str, resource: Any, cleanup: callable = None):
        """Context manager for resource management."""
        self.register_resource(name, resource, cleanup)
        try:
            yield resource
        finally:
            if cleanup:
                cleanup()

# Metrics Collector
class MetricsCollector:
    """Metrics collector for system metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, List[float]] = {}
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        if name not in self._counters:
            self._counters[name] = 0
        self._counters[name] += value
    
    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram value."""
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)
    
    def set_gauge(self, name: str, value: Any) -> None:
        """Set a gauge metric."""
        self._metrics[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            'counters': self._counters.copy(),
            'histograms': self._histograms.copy(),
            'gauges': self._metrics.copy()
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._histograms.clear()
        self._metrics.clear()

# Health Check System
class HealthChecker:
    """Health check system."""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._status: Dict[str, str] = {}
    
    def register_check(self, name: str, check_func: callable) -> None:
        """Register a health check."""
        self._checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self._checks.items():
            try:
                result = check_func()
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'result': result
                }
                if not result:
                    overall_status = "unhealthy"
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
                overall_status = "unhealthy"
        
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': time.time()
        }

# Base PiMoE System Interface
class BasePiMoESystem(ABC):
    """Base PiMoE system interface."""
    
    def __init__(self, config: BaseConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the system."""
        pass
    
    @abstractmethod
    def process_request(self, request_data: RequestData) -> ResponseData:
        """Process a request."""
        pass
    
    @abstractmethod
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the system."""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if system is initialized."""
        return self._initialized

# Utility Functions
def create_service_factory() -> ServiceFactory:
    """Create a configured service factory."""
    factory = ServiceFactory()
    return factory

def create_di_container() -> DIContainer:
    """Create a dependency injection container."""
    return DIContainer()

def create_event_bus() -> EventBus:
    """Create an event bus."""
    return EventBus()

def create_resource_manager(config: BaseConfig) -> ResourceManager:
    """Create a resource manager."""
    return ResourceManager(config)

def create_metrics_collector() -> MetricsCollector:
    """Create a metrics collector."""
    return MetricsCollector()

def create_health_checker() -> HealthChecker:
    """Create a health checker."""
    return HealthChecker()




