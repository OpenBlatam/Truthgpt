"""
Unit tests for Plugin System
"""

import unittest
try:
    from ..plugin.plugin_system import (
        PluginConfig, PluginManager, PluginRegistry, create_plugin_manager, plugin_compilation_context
    )
except ImportError:
    from compiler.plugin.plugin_system import (
        PluginConfig, PluginManager, PluginRegistry, create_plugin_manager, plugin_compilation_context
    )

class TestPluginSystem(unittest.TestCase):
    """Test cases for plugin system."""

    def test_plugin_config(self):
        config = PluginConfig(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin"
        )
        self.assertEqual(config.name, "test_plugin")
        self.assertEqual(config.version, "1.0.0")
        self.assertEqual(config.description, "Test plugin")
        self.assertTrue(config.enabled)

    def test_plugin_manager_creation(self):
        manager = create_plugin_manager()
        self.assertIsNotNone(manager)
        self.assertEqual(len(manager.get_active_plugins()), 0)
        self.assertEqual(len(manager.get_registered_plugins()), 0)

    def test_plugin_context(self):
        manager = create_plugin_manager()
        with plugin_compilation_context(manager) as ctx:
            self.assertIsNotNone(ctx)

class TestPluginManager(unittest.TestCase):
    def test_manager(self):
        manager = PluginManager()
        self.assertEqual(len(manager.get_registered_plugins()), 0)

class TestPluginRegistry(unittest.TestCase):
    def test_registry(self):
        registry = PluginRegistry()
        self.assertEqual(len(registry.get_available_plugins()), 0)

def test_plugin_system():
    tc = TestPluginSystem()
    tc.test_plugin_config()
    tc.test_plugin_manager_creation()

def test_plugin_context():
    manager = create_plugin_manager()
    with plugin_compilation_context(manager) as ctx:
        assert ctx is not None
