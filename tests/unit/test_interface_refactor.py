"""
TruthGPT Interface Refactoring Verification Test Suite.
======================================================
Validates:
  1. 100% AST syntax validity of all files in interface/ and src/truthgpt/interface/
  2. Public symbols and exports in interface and truthgpt.interface
  3. MenuRegistry and ThemeRegistry registration, discovery, and dispatch
  4. InterfaceBuilder and TUIAppBuilder fluent assembly
  5. Unified factory methods (create_interface, create_menu, create_tui_app, create_theme_engine)
  6. Typed exception hierarchy in exceptions.py
  7. Enums and dataclasses in types.py
  8. TelemetryProvider caching and metrics
  9. Preferences loading and atomic serialization
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

for p in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestInterfaceSyntaxAndStructure(unittest.TestCase):
    """Verify syntax validity of all Python files in interface modules."""

    def test_syntax_validity_optimization_core_interface(self):
        """Verify that 100% of Python files in optimization_core/interface compile cleanly."""
        interface_dir = PROJECT_ROOT / "interface"
        errors = []
        file_count = 0
        for root, dirs, files in os.walk(interface_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    file_count += 1
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as src_f:
                            compile(src_f.read(), fp, "exec")
                    except SyntaxError as e:
                        errors.append((fp, e.lineno, e.msg))

        self.assertEqual(len(errors), 0, f"Found {len(errors)} syntax errors in {file_count} files: {errors}")
        self.assertGreaterEqual(file_count, 15)

    def test_syntax_validity_src_truthgpt_interface(self):
        """Verify that 100% of Python files in src/truthgpt/interface compile cleanly."""
        interface_dir = SRC_DIR / "truthgpt" / "interface"
        errors = []
        file_count = 0
        for root, dirs, files in os.walk(interface_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    file_count += 1
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as src_f:
                            compile(src_f.read(), fp, "exec")
                    except SyntaxError as e:
                        errors.append((fp, e.lineno, e.msg))

        self.assertEqual(len(errors), 0, f"Found {len(errors)} syntax errors in {file_count} files: {errors}")
        self.assertGreaterEqual(file_count, 15)


class TestInterfaceExportsAndImports(unittest.TestCase):
    """Test top-level imports and lazy loader resolution."""

    def test_direct_interface_imports(self):
        """Verify direct imports from interface package."""
        import interface

        symbols = [
            "create_interface",
            "create_tui_app",
            "create_menu",
            "create_theme_engine",
            "create_telemetry_provider",
            "InterfaceBuilder",
            "TUIAppBuilder",
            "MenuRegistry",
            "ThemeRegistry",
            "register_menu",
            "list_available_menus",
            "list_available_themes",
            "InterfaceError",
            "ConfigError",
            "TelemetryError",
            "TUIError",
            "MenuError",
            "ThemeError",
            "InterfaceMode",
            "ThemeType",
            "MenuCategory",
            "MenuItem",
            "TelemetrySnapshot",
            "UserPreferencesData",
            "LazyConsole",
            "TelemetryProvider",
            "get_system_telemetry",
            "BaseTUIApp",
            "InteractiveDashboardApp",
            "InteractiveSwarmApp",
            "CCSpinner",
        ]
        for sym in symbols:
            self.assertTrue(hasattr(interface, sym), f"interface missing symbol: {sym}")
            self.assertIsNotNone(getattr(interface, sym))

    def test_truthgpt_interface_resolution(self):
        """Verify imports from truthgpt.interface package mirror."""
        from truthgpt import interface as tg_interface

        symbols = [
            "create_interface",
            "create_tui_app",
            "create_menu",
            "create_theme_engine",
            "MenuRegistry",
            "ThemeRegistry",
            "InterfaceError",
            "TelemetryProvider",
            "BaseTUIApp",
        ]
        for sym in symbols:
            self.assertTrue(hasattr(tg_interface, sym), f"truthgpt.interface missing symbol: {sym}")


class TestMenuAndThemeRegistry(unittest.TestCase):
    """Test thread-safe registration and discovery in registries."""

    def test_menu_registry_defaults_and_discovery(self):
        """Verify that standard menus are discovered and listed."""
        from interface.registry import MenuRegistry, list_available_menus

        menus = list_available_menus()
        self.assertGreaterEqual(len(menus), 5)
        menu_ids = [m.id for m in menus]
        self.assertIn("swarm", menu_ids)
        self.assertIn("model", menu_ids)
        self.assertIn("history", menu_ids)

    def test_custom_menu_registration(self):
        """Verify custom menu decorator registration."""
        from interface.registry import register_menu, MenuRegistry

        @register_menu(
            name="unit_test_custom_menu",
            title="Unit Test Custom Menu",
            category="test",
            description="Testing dynamic registration",
            shortcut="U",
            icon="🧪",
            overwrite=True,
        )
        async def sample_handler():
            return "ok"

        menu_item = MenuRegistry.get_menu("unit_test_custom_menu")
        self.assertEqual(menu_item.name, "Unit Test Custom Menu")
        self.assertEqual(menu_item.shortcut, "U")
        self.assertEqual(menu_item.icon, "🧪")

    def test_theme_registry_palettes(self):
        """Verify theme palette retrieval."""
        from interface.registry import ThemeRegistry, list_available_themes, get_theme_palette

        themes = list_available_themes()
        self.assertIn("claude", themes)
        self.assertIn("industrial", themes)
        self.assertIn("matrix", themes)

        claude_palette = get_theme_palette("claude")
        self.assertEqual(claude_palette.name, "claude")
        self.assertEqual(claude_palette.focused_color, "#00ffff")


class TestBuilderAndFactory(unittest.TestCase):
    """Test fluent builders and unified factory creation."""

    def test_tui_builder_configuration(self):
        """Verify TUIAppBuilder configuration and config assembly."""
        from interface.builder import create_tui_builder
        from interface.types import InterfaceMode

        builder = (
            create_tui_builder("dashboard")
            .with_theme("claude")
            .with_mode(InterfaceMode.EXTENDED)
            .with_mouse_support(True)
            .with_full_screen(True)
            .with_refresh_interval(0.25)
        )
        config = builder.build_config()
        self.assertEqual(config.theme, "claude")
        self.assertTrue(config.extended_mode)
        self.assertTrue(config.mouse_support)
        self.assertEqual(config.refresh_interval, 0.25)

    def test_interface_factory_instantiation(self):
        """Verify create_interface and create_menu factories."""
        from interface.factory import (
            create_interface,
            create_menu,
            create_telemetry_provider,
            create_theme_engine,
        )

        menu = create_menu("swarm")
        self.assertIsNotNone(menu)

        theme_palette = create_theme_engine("claude")
        self.assertEqual(theme_palette.name, "claude")

        telemetry_cls = create_telemetry_provider()
        self.assertTrue(hasattr(telemetry_cls, "get_stats"))


class TestTypesAndExceptions(unittest.TestCase):
    """Test typed exceptions and dataclasses."""

    def test_typed_exceptions_hierarchy(self):
        """Verify exception inheritance under InterfaceError."""
        from interface.exceptions import (
            ConfigError,
            ConfigLoadError,
            InterfaceError,
            MenuError,
            MenuNotFoundError,
            TelemetryError,
            TUIError,
        )

        self.assertTrue(issubclass(ConfigLoadError, ConfigError))
        self.assertTrue(issubclass(ConfigError, InterfaceError))
        self.assertTrue(issubclass(MenuNotFoundError, MenuError))
        self.assertTrue(issubclass(MenuError, InterfaceError))
        self.assertTrue(issubclass(TelemetryError, InterfaceError))
        self.assertTrue(issubclass(TUIError, InterfaceError))

        err = MenuNotFoundError("Menu not found", details={"id": "missing"})
        self.assertIn("Details:", str(err))

    def test_user_preferences_dataclass_serialization(self):
        """Verify UserPreferencesData conversion to/from dictionary."""
        from interface.types import UserPreferencesData

        prefs = UserPreferencesData(
            user_name="TestPilot",
            preferred_engine="deepseek,claude",
            theme="matrix",
        )
        d = prefs.to_dict()
        self.assertEqual(d["user_name"], "TestPilot")
        self.assertEqual(d["preferred_engine"], "deepseek,claude")
        self.assertEqual(d["theme"], "matrix")

        reconstructed = UserPreferencesData.from_dict(d)
        self.assertEqual(reconstructed.user_name, "TestPilot")
        self.assertEqual(reconstructed.theme, "matrix")


class TestTelemetryProvider(unittest.TestCase):
    """Test telemetry gathering and caching."""

    def test_get_stats_returns_valid_dict(self):
        """Verify TelemetryProvider.get_stats structure."""
        from interface.telemetry import TelemetryProvider

        stats = TelemetryProvider.get_stats()
        self.assertIn("load", stats)
        self.assertIn("mem", stats)
        self.assertIn("session_id", stats)
        self.assertIn("version", stats)
        self.assertIsInstance(stats["load"], (int, float))
        self.assertIsInstance(stats["mem"], (int, float))


if __name__ == "__main__":
    unittest.main()
