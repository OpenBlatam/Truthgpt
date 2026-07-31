"""
Plugin Loader module for TruthGPT Compiler
Dynamic and static plugin loading infrastructure
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Optional, Any, Type
from contextlib import contextmanager

from .plugin_system import CompilerPlugin, PluginConfig

logger = logging.getLogger(__name__)


class PluginLoader:
    """Base class for compiler plugin loaders."""

    def load_plugin(self, source: str) -> Optional[CompilerPlugin]:
        """Load plugin from source descriptor."""
        raise NotImplementedError


class DynamicPluginLoader(PluginLoader):
    """Loader for dynamically loading Python modules as plugins."""

    def load_plugin_from_file(self, file_path: str) -> Optional[CompilerPlugin]:
        """Load plugin from file path."""
        if not os.path.exists(file_path):
            logger.error(f"Plugin file not found: {file_path}")
            return None
        
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Look for CompilerPlugin subclasses
        for attr in dir(mod):
            val = getattr(mod, attr)
            if isinstance(val, type) and issubclass(val, CompilerPlugin) and val is not CompilerPlugin:
                config = PluginConfig(name=attr, version="1.0.0", description="Dynamically loaded plugin")
                return val(config)
        return None


class StaticPluginLoader(PluginLoader):
    """Loader for statically registered plugin classes."""

    def __init__(self):
        self.registered_classes: Dict[str, Type[CompilerPlugin]] = {}

    def register(self, name: str, plugin_cls: Type[CompilerPlugin]):
        """Register plugin class."""
        self.registered_classes[name] = plugin_cls

    def load_plugin(self, name: str) -> Optional[CompilerPlugin]:
        """Instantiate registered plugin class."""
        if name in self.registered_classes:
            config = PluginConfig(name=name, version="1.0.0", description="Statically loaded plugin")
            return self.registered_classes[name](config)
        return None


def create_plugin_loader(loader_type: str = "dynamic") -> PluginLoader:
    """Factory function for PluginLoader."""
    if loader_type == "static":
        return StaticPluginLoader()
    return DynamicPluginLoader()


@contextmanager
def plugin_loading_context(loader_type: str = "dynamic"):
    """Context manager for plugin loading operations."""
    loader = create_plugin_loader(loader_type)
    try:
        yield loader
    finally:
        pass
