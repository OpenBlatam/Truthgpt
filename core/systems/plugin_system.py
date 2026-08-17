"""
Plugin system for extensible modular architecture.
Allows dynamic loading, topological dependency sorting, and registration of plugins.
"""
import logging
import importlib
import threading
from typing import Dict, List, Type, Optional, Any
from pathlib import Path
from abc import ABC, abstractmethod

from .service_registry import ServiceRegistry
from ..common_runtime.exceptions import PluginError

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @abstractmethod
    def initialize(self, registry: ServiceRegistry) -> None:
        """
        Initialize plugin and register services.
        
        Args:
            registry: Service registry
        """
        pass
    
    def activate(self) -> None:
        """Called when plugin is activated."""
        logger.info(f"Plugin '{self.name}' activated")
    
    def deactivate(self) -> None:
        """Called when plugin is deactivated."""
        logger.info(f"Plugin '{self.name}' deactivated")
    
    def get_dependencies(self) -> List[str]:
        """
        Get list of plugin dependencies.
        
        Returns:
            List of required plugin names
        """
        return []


class PluginManager:
    """
    Manages plugin loading, activation, and lifecycle with thread safety.
    """
    
    def __init__(self, registry: Optional[ServiceRegistry] = None):
        """
        Initialize plugin manager.
        
        Args:
            registry: Service registry (uses global if None)
        """
        self.registry = registry or ServiceRegistry()
        self._plugins: Dict[str, Plugin] = {}
        self._active_plugins: List[str] = []
        self._plugin_paths: Dict[str, Path] = {}
        self._lock = threading.RLock()
    
    def register_plugin(
        self,
        plugin: Plugin,
        auto_activate: bool = True
    ) -> None:
        """Register a plugin."""
        with self._lock:
            if plugin.name in self._plugins:
                logger.warning(f"Plugin '{plugin.name}' already registered")
                return
            
            dependencies = plugin.get_dependencies()
            missing_deps = [dep for dep in dependencies if dep not in self._plugins]
            if missing_deps:
                raise PluginError(
                    f"Plugin '{plugin.name}' has unmet dependencies: {missing_deps}"
                )
            
            self._plugins[plugin.name] = plugin
            
            if auto_activate:
                self.activate_plugin(plugin.name)
            else:
                logger.info(f"Plugin '{plugin.name}' registered (not activated)")
    
    def load_plugin_from_module(
        self,
        module_path: str,
        plugin_class_name: str = "Plugin",
        auto_activate: bool = True
    ) -> Plugin:
        """Load plugin from a Python module."""
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, plugin_class_name)
            plugin = plugin_class()
            
            self.register_plugin(plugin, auto_activate=auto_activate)
            return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_path}: {e}", exc_info=True)
            raise PluginError(f"Failed to load plugin from {module_path}: {e}") from e
    
    def load_plugins_from_directory(
        self,
        directory: str,
        auto_activate: bool = True
    ) -> List[Plugin]:
        """Load all plugins from a directory."""
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return []
        
        loaded_plugins = []
        with self._lock:
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                
                module_name = plugin_file.stem
                module_path = f"{plugin_dir.name}.{module_name}"
                
                try:
                    plugin = self.load_plugin_from_module(
                        module_path,
                        auto_activate=auto_activate
                    )
                    loaded_plugins.append(plugin)
                    self._plugin_paths[plugin.name] = plugin_file
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
        
        return loaded_plugins
    
    def activate_plugin(self, plugin_name: str) -> None:
        """Activate a plugin."""
        with self._lock:
            if plugin_name not in self._plugins:
                raise PluginError(f"Plugin '{plugin_name}' not found")
            
            if plugin_name in self._active_plugins:
                logger.warning(f"Plugin '{plugin_name}' already active")
                return
            
            plugin = self._plugins[plugin_name]
            plugin.initialize(self.registry)
            plugin.activate()
            self._active_plugins.append(plugin_name)
            
            logger.info(f"Plugin '{plugin_name}' activated")
    
    def deactivate_plugin(self, plugin_name: str) -> None:
        """Deactivate a plugin."""
        with self._lock:
            if plugin_name not in self._active_plugins:
                logger.warning(f"Plugin '{plugin_name}' not active")
                return
            
            plugin = self._plugins[plugin_name]
            plugin.deactivate()
            self._active_plugins.remove(plugin_name)
            
            logger.info(f"Plugin '{plugin_name}' deactivated")
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        with self._lock:
            return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        with self._lock:
            return list(self._plugins.keys())
    
    def list_active_plugins(self) -> List[str]:
        """List all active plugins."""
        with self._lock:
            return self._active_plugins.copy()


# Global plugin manager
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager."""
    return _plugin_manager


class ExamplePlugin(Plugin):
    """Example plugin implementation."""
    
    @property
    def name(self) -> str:
        return "example_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self, registry: ServiceRegistry) -> None:
        """Initialize the plugin."""
        registry.register("example_service", self._create_service, singleton=True)
        logger.info("Example plugin initialized")
    
    def _create_service(self):
        """Create example service."""
        return {"status": "ready"}



