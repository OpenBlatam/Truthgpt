"""
Service Registry with Dependency Injection for maximum modularity.
Enables loose coupling between components through service registration.
"""
import logging
import threading
import inspect
from typing import Dict, Any, Optional, Type, Callable, TypeVar, Generic, List, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from .exceptions import ServiceRegistryError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceRegistry:
    """
    Central registry for services with dependency injection.
    Implements thread-safe singleton pattern for global access.
    """
    
    _instance: Optional['ServiceRegistry'] = None
    _lock = threading.RLock()
    
    def __new__(cls) -> 'ServiceRegistry':
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._services: Dict[str, Any] = {}
                instance._factories: Dict[str, Callable] = {}
                instance._singletons: Dict[str, Any] = {}
                instance._dependencies: Dict[str, List[str]] = {}
                cls._instance = instance
            return cls._instance
    
    def register(
        self,
        name: str,
        service: Any,
        singleton: bool = False,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a service.
        
        Args:
            name: Service name
            service: Service instance or class or factory callable
            singleton: If True, service will be instantiated once
            dependencies: List of service names this service depends on
        """
        with self._lock:
            if dependencies:
                self._dependencies[name] = list(dependencies)
            
            if singleton and callable(service) and not isinstance(service, type):
                self._factories[name] = service
            elif singleton:
                self._factories[name] = service
            else:
                self._services[name] = service
            
            logger.debug(f"Service registered: {name} (singleton={singleton})")
    
    def get(self, name: str, _resolving: Optional[Set[str]] = None, **kwargs) -> Any:
        """
        Get a service instance with cycle detection.
        
        Args:
            name: Service name
            **kwargs: Arguments for factory functions
        
        Returns:
            Service instance
        """
        with self._lock:
            if _resolving is None:
                _resolving = set()
            
            if name in _resolving:
                chain = " -> ".join(list(_resolving) + [name])
                raise ServiceRegistryError(f"Circular dependency detected: {chain}")
            
            _resolving.add(name)
            
            # Resolve dependencies first if declared
            if name in self._dependencies:
                for dep in self._dependencies[name]:
                    if dep not in self._singletons and dep not in self._services and dep not in self._factories:
                        raise ServiceRegistryError(f"Service '{name}' missing required dependency '{dep}'")
            
            try:
                # Check singletons first
                if name in self._singletons:
                    return self._singletons[name]
                
                # Check factories (singleton services)
                if name in self._factories:
                    factory = self._factories[name]
                    if callable(factory):
                        instance = factory(**kwargs) if kwargs else factory()
                    else:
                        instance = factory
                    
                    self._singletons[name] = instance
                    return instance
                
                # Check regular services
                if name in self._services:
                    service = self._services[name]
                    if isinstance(service, type):
                        return service(**kwargs) if kwargs else service()
                    return service
                
                raise ServiceRegistryError(f"Service '{name}' not found in registry")
            finally:
                _resolving.remove(name)
    
    def unregister(self, name: str) -> None:
        """Unregister a service."""
        with self._lock:
            self._services.pop(name, None)
            self._factories.pop(name, None)
            self._singletons.pop(name, None)
            self._dependencies.pop(name, None)
            logger.debug(f"Service unregistered: {name}")
    
    def clear(self) -> None:
        """Clear all services."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            self._dependencies.clear()
            logger.info("Service registry cleared")
    
    def list_services(self) -> List[str]:
        """List all registered service names."""
        with self._lock:
            all_services = set(self._services.keys())
            all_services.update(self._factories.keys())
            all_services.update(self._singletons.keys())
            return sorted(all_services)


# Global registry instance
registry = ServiceRegistry()


def register_service(name: str, singleton: bool = False, dependencies: Optional[List[str]] = None):
    """
    Decorator to register a service.
    
    Usage:
        @register_service("my_service", singleton=True)
        class MyService:
            pass
    """
    def decorator(cls_or_func):
        registry.register(name, cls_or_func, singleton=singleton, dependencies=dependencies)
        return cls_or_func
    return decorator


def get_service(name: str, **kwargs) -> Any:
    """Get a service from the registry."""
    return registry.get(name, **kwargs)


@dataclass
class ServiceDescriptor:
    """Descriptor for service metadata."""
    name: str
    service_type: Type
    singleton: bool = False
    dependencies: List[str] = field(default_factory=list)


class ServiceProvider(ABC):
    """Base class for service providers."""
    
    @abstractmethod
    def register_services(self, registry: ServiceRegistry) -> None:
        """Register services with the registry."""
        pass


class ServiceContainer:
    """
    Container for managing services with dependency injection.
    """
    
    def __init__(self):
        self._registry = ServiceRegistry()
        self._providers: List[ServiceProvider] = []
    
    def add_provider(self, provider: ServiceProvider) -> None:
        """Add a service provider."""
        self._providers.append(provider)
        provider.register_services(self._registry)
    
    def register(
        self,
        name: str,
        service: Any,
        singleton: bool = False,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a service."""
        self._registry.register(name, service, singleton=singleton, dependencies=dependencies)
    
    def get(self, name: str, **kwargs) -> Any:
        """Get a service."""
        return self._registry.get(name, **kwargs)
    
    def build(self, service_class: Type[T], **kwargs) -> T:
        """
        Build a service instance with dependency injection.
        """
        sig = inspect.signature(service_class.__init__)
        
        resolved_kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            if param_name in kwargs:
                resolved_kwargs[param_name] = kwargs[param_name]
            elif param.annotation != inspect.Parameter.empty:
                type_name = param.annotation.__name__ if hasattr(param.annotation, "__name__") else None
                if type_name and type_name in self._registry.list_services():
                    resolved_kwargs[param_name] = self._registry.get(type_name)
        
        resolved_kwargs.update(kwargs)
        return service_class(**resolved_kwargs)



