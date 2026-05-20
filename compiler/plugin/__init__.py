"""
Plugin System for TruthGPT Compiler
Extensible plugin architecture for compiler components
"""

from .plugin_system import (
    CompilerPlugin, PluginManager, PluginRegistry, PluginInterface,
    PluginConfig, PluginResult, PluginStatus,
    create_plugin_manager, plugin_compilation_context
)

from .plugin_loader import (
    PluginLoader, DynamicPluginLoader, StaticPluginLoader,
    create_plugin_loader, plugin_loading_context
)

from .plugin_validator import (
    PluginValidator, ValidationResult, ValidationError,
    create_plugin_validator, validation_context
)

__all__ = [
    'CompilerPlugin',
    'PluginManager',
    'PluginRegistry',
    'PluginInterface',
    'PluginConfig',
    'PluginResult',
    'PluginStatus',
    'create_plugin_manager',
    'plugin_compilation_context',
    'PluginLoader',
    'DynamicPluginLoader',
    'StaticPluginLoader',
    'create_plugin_loader',
    'plugin_loading_context',
    'PluginValidator',
    'ValidationResult',
    'ValidationError',
    'create_plugin_validator',
    'validation_context'
]





