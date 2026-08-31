"""
Comprehensive Verification Test Suite for Refactored TruthGPT Interface Subsystem.
==================================================================================
Tests:
  1. Package imports across canonical and aliased namespaces (interface vs optimization_core.interface)
  2. Configuration management, preferences persistence, defaults, and corruption recovery
  3. Telemetry provider stats gathering, caching, and budget tracking
  4. Global event logging, activity records, and session ledger persistence
  5. Theming color resolution, header renderers, and styled panel construction
  6. Multi-language code extraction and mission output export
  7. MenuRegistry and ThemeRegistry dynamic registration, discovery, and async dispatch
  8. Domain data types, enums, schemas, and dataclasses
  9. PEP 544 protocol contracts and abstract base classes
  10. Domain exception hierarchy and error handling
"""
import asyncio
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

import interface
from interface.types import (
    UITheme,
    InterfaceMode,
    EnsembleMode,
    EngineProvider,
    LogStatus,
    LogKind,
    ExportFormat,
    UserPreferences,
    ApiKeysConfig,
    ApiCreditsConfig,
    SystemLogEntry,
    ActivityLogEntry,
    TelemetrySnapshot,
    ThemePalette,
    TUIConfiguration,
    MenuItem,
)
from interface.exceptions import (
    InterfaceError,
    ConfigurationError,
    PreferencesCorruptionError,
    TelemetryError,
    ThemingError,
    ThemeNotFoundError,
    MenuError,
    MenuNotFoundError,
    InvalidMenuChoiceError,
    UserInputError,
    ExportError,
    TUIAppError,
)
from interface.interfaces import (
    ITelemetryProvider,
    IConsoleManager,
    IThemeRenderer,
    IHistoryLedger,
    IExportManager,
    IMenuHandler,
    ITUIApp,
    BaseTelemetryProvider,
    BaseThemeEngine,
    BaseHistoryLedger,
    BaseExportManager,
    BaseMenu,
    BaseTUIComponent,
)
from interface.registry import (
    MenuRegistry,
    ThemeRegistry,
    menu_registry,
    theme_registry,
)
from interface.config import (
    DEFAULT_USER_PREFS,
    load_user_prefs,
    save_user_prefs,
)
from interface.telemetry import (
    TelemetryProvider,
    get_system_telemetry,
    get_real_budget_stats,
)
from interface.state import (
    SYSTEM_LOGS,
    system_history,
    log_event,
    log_activity,
    claude_log_event,
)
from interface.theming import (
    get_theme_color,
    get_theme_panel,
    get_header,
    get_claude_header,
)
from interface.export_utils import (
    extract_target_directory,
    extract_and_save_code_blocks,
)
from interface.factory import (
    create_interface,
    create_menu,
    create_telemetry_provider,
    create_theme_engine,
    create_tui_app,
)
from interface.builder import (
    InterfaceBuilder,
    TUIAppBuilder,
    create_interface_builder,
    create_tui_builder,
)


class TestInterfaceRefactor(unittest.TestCase):
    """Test suite covering the entire refactored TruthGPT Interface subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_truthgpt_interface_")
        self.temp_path = Path(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. Package & Namespace Tests
    # -----------------------------------------------------------------------

    def test_version_and_namespace_aliasing(self) -> None:
        """Verify package version and sys.modules aliasing."""
        self.assertEqual(interface.__version__, "5.9.0")
        import optimization_core.interface as oi
        self.assertEqual(oi.__version__, "5.9.0")
        self.assertIs(interface.load_user_prefs, oi.load_user_prefs)
        self.assertIs(interface.TelemetryProvider, oi.TelemetryProvider)

    # -----------------------------------------------------------------------
    # 2. Configuration & Preferences Tests
    # -----------------------------------------------------------------------

    def test_user_preferences_load_and_save(self) -> None:
        """Verify preferences load, save, and schema validation."""
        cfg_file = self.temp_path / "user_prefs.json"
        
        # Test loading from non-existent file returns defaults
        prefs = load_user_prefs(path=cfg_file)
        self.assertEqual(prefs["user_name"], DEFAULT_USER_PREFS["user_name"])
        self.assertEqual(prefs["preferred_engine"], "deepseek")

        # Test mutation and persistence
        prefs["user_name"] = "Alice_Researcher"
        prefs["theme"] = "cyber"
        save_user_prefs(prefs, path=cfg_file)
        self.assertTrue(cfg_file.exists())

        # Test reload
        reloaded = load_user_prefs(path=cfg_file)
        self.assertEqual(reloaded["user_name"], "Alice_Researcher")
        self.assertEqual(reloaded["theme"], "cyber")

    def test_corrupted_preferences_recovery(self) -> None:
        """Verify self-healing recovery when preferences file is corrupted."""
        cfg_file = self.temp_path / "corrupted_prefs.json"
        cfg_file.write_text("{invalid json content ::--", encoding="utf-8")

        recovered = load_user_prefs(path=cfg_file)
        self.assertEqual(recovered["user_name"], DEFAULT_USER_PREFS["user_name"])
        # Corrupted file should be backed up as .corrupt
        self.assertTrue(cfg_file.with_suffix(".corrupt").exists())

    # -----------------------------------------------------------------------
    # 3. Telemetry & Metrics Tests
    # -----------------------------------------------------------------------

    def test_telemetry_provider_and_budget_stats(self) -> None:
        """Verify system metrics gathering, session ID generation, and caching."""
        session_id = TelemetryProvider.get_session_id()
        self.assertTrue(len(session_id) >= 4)

        stats = TelemetryProvider.get_stats()
        self.assertIn("load", stats)
        self.assertIn("mem", stats)
        self.assertIn("session_id", stats)
        self.assertEqual(stats["session_id"], session_id)

        # Proxy function test
        proxy_stats = get_system_telemetry()
        self.assertEqual(proxy_stats["session_id"], session_id)

        # Budget stats test
        budget = get_real_budget_stats()
        self.assertIn("total_usd", budget)
        self.assertIn("savings_usd", budget)

    # -----------------------------------------------------------------------
    # 4. State & Event Logging Tests
    # -----------------------------------------------------------------------

    def test_event_and_activity_logging(self) -> None:
        """Verify system event and module activity ledger recording."""
        initial_log_count = len(SYSTEM_LOGS)
        initial_hist_count = len(system_history)

        log_event(layer="TEST_LAYER", event="Unit test initialization", status="DONE")
        self.assertEqual(len(SYSTEM_LOGS), initial_log_count + 1)
        last_log = SYSTEM_LOGS[-1]
        self.assertEqual(last_log["layer"], "TEST_LAYER")
        self.assertEqual(last_log["status"], "DONE")

        log_activity(module="TestModule", task="Run regression checks", status="Completed")
        self.assertEqual(len(system_history), initial_hist_count + 1)
        last_hist = system_history[-1]
        self.assertEqual(last_hist["module"], "TestModule")
        self.assertEqual(last_hist["status"], "Completed")

    # -----------------------------------------------------------------------
    # 5. Theming & Header Renderer Tests
    # -----------------------------------------------------------------------

    def test_theming_and_headers(self) -> None:
        """Verify color resolution, theme panels, and header banners."""
        color = get_theme_color()
        self.assertIn(color, ["plum1", "orange3", "cyan", "green"])

        panel = get_theme_panel("Test Panel Content", title="Test Header")
        self.assertIsNotNone(panel)

        header = get_header()
        self.assertIsNotNone(header)

        claude_header = get_claude_header(["Test update 1", "Test update 2"])
        self.assertIsNotNone(claude_header)

    # -----------------------------------------------------------------------
    # 6. Code Extraction & Exporter Tests
    # -----------------------------------------------------------------------

    def test_code_block_extraction(self) -> None:
        """Verify automated multi-language markdown code block parser."""
        sample_markdown = """
# Mission Report
Here is Python code:
```python
def add(a, b):
    return a + b
```
And here is Rust code:
```rust
fn main() {
    println!("Hello World");
}
```
"""
        export_target = self.temp_path / "extracted_code"
        saved = extract_and_save_code_blocks(sample_markdown, target_dir=export_target, prefix="snippet")
        self.assertEqual(len(saved), 2)
        
        py_files = list(export_target.glob("*.py"))
        rs_files = list(export_target.glob("*.rs"))
        self.assertEqual(len(py_files), 1)
        self.assertEqual(len(rs_files), 1)
        self.assertIn("def add", py_files[0].read_text(encoding="utf-8"))
        self.assertIn("fn main", rs_files[0].read_text(encoding="utf-8"))

    def test_extract_target_directory(self) -> None:
        """Verify target directory extraction from natural language queries."""
        query = f"Please generate tests and write outputs to {self.temp_dir} now"
        extracted = extract_target_directory(query)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.resolve(), self.temp_path.resolve())

    # -----------------------------------------------------------------------
    # 7. MenuRegistry & ThemeRegistry Tests
    # -----------------------------------------------------------------------

    def test_theme_registry(self) -> None:
        """Verify ThemeRegistry theme retrieval and palette queries."""
        theme_reg = ThemeRegistry.get_instance()
        self.assertTrue(len(theme_reg.list_themes()) >= 5)

        claude_info = theme_reg.get("claude")
        self.assertEqual(claude_info["primary_color"], "plum1")
        self.assertTrue(claude_info["is_claude_style"])

        industrial_info = theme_reg.get("industrial")
        self.assertEqual(industrial_info["primary_color"], "orange3")
        self.assertFalse(industrial_info["is_claude_style"])

        # Fallback to industrial on unknown theme
        unknown = theme_reg.get("non_existent_theme")
        self.assertEqual(unknown["name"], "industrial")

    def test_menu_registry_dispatch(self) -> None:
        """Verify MenuRegistry registration and async command routing."""
        reg = MenuRegistry.get_instance()
        
        async def custom_test_handler(x: int, y: int) -> int:
            return x + y

        reg.register("TEST_ROUTE", label="Test Route", handler=custom_test_handler, category="test")
        item = reg.get("TEST_ROUTE")
        self.assertIsNotNone(item)
        self.assertEqual(item.label, "Test Route")

        # Dispatch test
        result = asyncio.run(reg.dispatch("TEST_ROUTE", 10, 25))
        self.assertEqual(result, 35)

        # Invalid route dispatch test
        with self.assertRaises(InvalidMenuChoiceError):
            asyncio.run(reg.dispatch("NON_EXISTENT_ROUTE_9999"))

    # -----------------------------------------------------------------------
    # 8. Domain Types & Schemas Tests
    # -----------------------------------------------------------------------

    def test_domain_dataclasses_and_enums(self) -> None:
        """Verify UserPreferences, SystemLogEntry, and enum serialization."""
        theme = UITheme.from_str("minimalist")
        self.assertEqual(theme, UITheme.MINIMALIST)
        self.assertTrue(theme.is_claude_style)
        self.assertEqual(theme.primary_color, "plum1")

        ensemble = EnsembleMode.from_str("bayesian")
        self.assertEqual(ensemble, EnsembleMode.BAYESIAN)

        provider = EngineProvider.from_str("deepseek")
        self.assertEqual(provider, EngineProvider.DEEPSEEK)

        user_prefs = UserPreferences(
            user_name="Bob",
            preferred_engine="openrouter",
            theme="cyber",
            api_keys=ApiKeysConfig(openai="sk-test-key"),
            api_credits=ApiCreditsConfig(claude=15.50),
        )
        prefs_dict = user_prefs.to_dict()
        self.assertEqual(prefs_dict["user_name"], "Bob")
        self.assertEqual(prefs_dict["api_keys"]["openai"], "sk-test-key")
        self.assertEqual(prefs_dict["api_credits"]["claude"], 15.50)

        # Roundtrip from dict
        roundtrip = UserPreferences.from_dict(prefs_dict)
        self.assertEqual(roundtrip.user_name, "Bob")
        self.assertEqual(roundtrip.api_keys.openai, "sk-test-key")
        self.assertEqual(roundtrip.api_credits.claude, 15.50)

    # -----------------------------------------------------------------------
    # 9. Exception Hierarchy Tests
    # -----------------------------------------------------------------------

    def test_exception_hierarchy(self) -> None:
        """Verify fine-grained domain exceptions inherit correctly from InterfaceError."""
        self.assertTrue(issubclass(ConfigurationError, InterfaceError))
        self.assertTrue(issubclass(PreferencesCorruptionError, ConfigurationError))
        self.assertTrue(issubclass(TelemetryError, InterfaceError))
        self.assertTrue(issubclass(ThemingError, InterfaceError))
        self.assertTrue(issubclass(ThemeNotFoundError, ThemingError))
        self.assertTrue(issubclass(MenuError, InterfaceError))
        self.assertTrue(issubclass(InvalidMenuChoiceError, MenuError))
        self.assertTrue(issubclass(UserInputError, InterfaceError))
        self.assertTrue(issubclass(ExportError, InterfaceError))
        self.assertTrue(issubclass(TUIAppError, InterfaceError))

        # Test instantiation with details
        err = InvalidMenuChoiceError("Invalid selection", details={"choice": "99"})
        self.assertEqual(err.message, "Invalid selection")
        self.assertEqual(err.details, {"choice": "99"})
        self.assertIn("InvalidMenuChoiceError", repr(err))

    # -----------------------------------------------------------------------
    # 10. Builders & Unified Factory Tests
    # -----------------------------------------------------------------------

    def test_builders_and_factory(self) -> None:
        """Verify InterfaceBuilder, TUIAppBuilder, and factory constructors."""
        if_builder = create_interface_builder(title="Custom TruthGPT Interface")
        if_builder.with_theme("cyber")
        if_builder.with_mode(InterfaceMode.STANDARD)
        self.assertEqual(if_builder.title, "Custom TruthGPT Interface")

        tui_builder = create_tui_builder(app_type="dashboard")
        tui_builder.with_theme("claude")
        tui_builder.with_extended(True)
        config = tui_builder.build_config()
        self.assertTrue(config.extended_mode)
        self.assertEqual(config.theme, "claude")

        # Factory methods
        provider = create_telemetry_provider()
        self.assertIs(provider, TelemetryProvider)

        palette = create_theme_engine("claude")
        self.assertEqual(palette.primary_color, "plum1")


if __name__ == "__main__":
    unittest.main()
