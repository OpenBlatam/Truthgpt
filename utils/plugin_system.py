try:
    from modules.infrastructure.plugin_system import (
        PluginInfo,
        PluginRegistry,
        BasePlugin,
        register_plugin,
        get_plugin,
        list_plugins
    )
except (ImportError, ValueError):
    from ..modules.infrastructure.plugin_system import (
        PluginInfo,
        PluginRegistry,
        BasePlugin,
        register_plugin,
        get_plugin,
        list_plugins
    )

__all__ = [
    'PluginInfo',
    'PluginRegistry',
    'BasePlugin',
    'register_plugin',
    'get_plugin',
    'list_plugins'
]
