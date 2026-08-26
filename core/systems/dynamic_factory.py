"""
Dynamic factory system with automatic registration.
Enables dynamic plugin-based component registration with thread safety.
"""
import logging
import inspect
import threading
import fnmatch
from typing import Dict, Type, TypeVar, Callable, Any, Optional, List
from abc import ABC
from ..common_runtime.exceptions import OptimizationCoreError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DynamicFactory:
    """
    Dynamic factory with automatic registration based on naming conventions
    and decorators. Thread-safe.
    """
    
    def __init__(self, base_class: Optional[Type] = None, name: Optional[str] = None):
        if isinstance(base_class, str) and name is None:
            self.name = base_class
            self.base_class = None
        else:
            self.base_class = base_class
            self.name = name or (base_class.__name__ if base_class else "dynamic_factory")
        self._registry: Dict[str, Type] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        name: str,
        component: Type[T],
        override: bool = False
    ) -> None:
        """Register a component class or instance."""
        with self._lock:
            if self.base_class and inspect.isclass(component) and not issubclass(component, self.base_class):
                raise OptimizationCoreError(
                    f"Component '{name}' must inherit from {self.base_class.__name__}"
                )
            
            if name in self._registry and not override:
                raise OptimizationCoreError(f"Component '{name}' already registered in factory")
            
            self._registry[name] = component
            logger.debug(f"Component '{name}' registered in factory")
    
    def register_factory(
        self,
        name: str,
        factory: Callable,
        override: bool = False
    ) -> None:
        """Register a factory callable."""
        with self._lock:
            if name in self._factories and not override:
                raise OptimizationCoreError(f"Factory callable '{name}' already registered")
            
            self._factories[name] = factory
            logger.debug(f"Factory callable '{name}' registered")
    
    def create(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        """Create a component instance."""
        with self._lock:
            if name in self._factories:
                factory_fn = self._factories[name]
                return factory_fn(*args, **kwargs)
            
            if name in self._registry:
                component_class = self._registry[name]
                if inspect.isclass(component_class):
                    return component_class(*args, **kwargs)
                return component_class
            
            raise OptimizationCoreError(f"Component '{name}' not found in factory")
    
    def list_components(self) -> List[str]:
        """List all registered component names."""
        with self._lock:
            components = set(self._registry.keys())
            components.update(self._factories.keys())
            return sorted(components)
    
    def auto_register_from_module(
        self,
        module: Any,
        name_pattern: Optional[str] = None
    ) -> None:
        """Automatically register components from a module."""
        with self._lock:
            for name, obj in inspect.getmembers(module):
                if not inspect.isclass(obj):
                    continue
                
                if self.base_class and not issubclass(obj, self.base_class):
                    continue
                
                if name_pattern:
                    if not fnmatch.fnmatch(name, name_pattern):
                        continue
                
                self.register(name.lower(), obj, override=True)
                logger.debug(f"Auto-registered component: {name}")


def factory(base_class: Optional[Type] = None) -> DynamicFactory:
    """Decorator / helper to create a factory instance."""
    return DynamicFactory(base_class=base_class)


def register_component(factory_instance: DynamicFactory, name: Optional[str] = None):
    """Decorator to register a class with a specific factory instance."""
    def decorator(cls):
        reg_name = name or cls.__name__.lower()
        factory_instance.register(reg_name, cls)
        return cls
    return decorator


class AutoRegisterMeta(type):
    """Metaclass for automatic factory registration."""
    def __new__(mcs, name, bases, namespace, factory_instance=None, register_name=None):
        cls = super().__new__(mcs, name, bases, namespace)
        if factory_instance and register_name:
            factory_instance.register(register_name or name.lower(), cls)
        return cls


_global_factories: Dict[str, DynamicFactory] = {}
_factory_lock = threading.RLock()


def get_factory(name: str) -> Optional[DynamicFactory]:
    """Get a global factory by name."""
    with _factory_lock:
        return _global_factories.get(name)


def create_factory(
    name: str,
    base_class: Optional[Type] = None
) -> DynamicFactory:
    """Create and register a global factory."""
    with _factory_lock:
        factory_instance = DynamicFactory(base_class=base_class)
        _global_factories[name] = factory_instance
        return factory_instance



