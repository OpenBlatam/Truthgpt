"""
Comprehensive Automated Test Suite for Enterprise Interface Subsystem Refactoring.
===================================================================================
Tests types, interfaces, exceptions, registries, builders, factories, theming,
telemetry, config, TUI lifecycle, export utilities, and cross-module aliasing.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test 1: Module Aliasing & Namespace Integration
# ---------------------------------------------------------------------------

def test_module_aliasing():
    """Verify bidirectional aliasing between interface and optimization_core.interface."""
    import interface
    import optimization_core.interface as o_iface

    assert interface is o_iface, "Namespaces must reference the exact same module object."
    assert hasattr(interface, "__version__"), "Must expose __version__."
    assert interface.__version__ in ("5.9.0", "2.5.0")
    assert len(dir(interface)) >= 100, "Must expose comprehensive public API surface."


# ---------------------------------------------------------------------------
# Test 2: Types, Enums & Dataclasses
# ---------------------------------------------------------------------------

def test_domain_types_and_enums():
    """Verify Enums, Dataclasses, and TypedDicts."""
    from interface.types import (
        ApiBalanceInfo,
        EnsembleMode,
        ErrorSeverity,
        ExportResult,
        MenuAction,
        MenuOption,
        PromptChoice,
        SessionState,
        SessionTelemetry,
        ThemeConfig,
        ThemePalette,
        ThemeType,
        UserPreferences,
    )

    # ThemeType enum
    assert ThemeType.CLAUDE.value == "claude"
    assert ThemeType.from_string("industrial") == ThemeType.INDUSTRIAL or ThemeType.from_string("claude") == ThemeType.CLAUDE

    # EnsembleMode enum
    assert EnsembleMode.RACE.value == "race"
    assert EnsembleMode.from_string("debate") == EnsembleMode.DEBATE

    # ErrorSeverity
    assert ErrorSeverity.ERROR.value == "ERROR"
    assert ErrorSeverity.CRITICAL.value == "CRITICAL"

    # ThemePalette & ThemeConfig
    palette = ThemePalette(name="claude", primary="plum1", border_style="plum1", focused_color="#00ffff")
    assert palette.name == "claude"
    assert palette.primary == "plum1"

    # UserPreferences dataclass serialization
    prefs = UserPreferences(
        user_name="Architect",
        preferred_engine="deepseek",
        theme="claude",
        continuous_mode=False,
    )
    prefs_dict = prefs.to_dict()
    assert prefs_dict["user_name"] == "Architect"
    assert prefs_dict["preferred_engine"] == "deepseek"

    deserialized = UserPreferences.from_dict(prefs_dict)
    assert deserialized.user_name == "Architect"
    assert deserialized.theme == "claude"

    # ExportResult
    res = ExportResult(export_path=Path("output.md"), code_blocks_extracted=3, success=True)
    assert res.success is True
    assert res.code_blocks_extracted == 3


# ---------------------------------------------------------------------------
# Test 3: Abstract Interfaces & Protocols Contract
# ---------------------------------------------------------------------------

def test_abstract_interfaces():
    """Verify ABCs and Protocols enforcement."""
    from interface.interfaces import (
        BaseExportHandler,
        BaseHistoryLedger,
        BaseInputHandler,
        BaseMenu,
        BasePreferenceManager,
        BaseTelemetryCollector,
        BaseThemeRenderer,
        BaseTUIComponent,
        IConsoleProvider,
        IMenuHandler,
        ITelemetryProvider,
        IThemingProvider,
        ITUIApp,
    )

    # Concrete test menu
    class TestMenu(BaseMenu):
        async def render_and_execute(self) -> str:
            return "executed"

    menu = TestMenu(title="Test Menu", category="Testing")
    menu.add_option("1", "Run Test", "Executes unit test", handler=lambda: "ok")
    menu.add_divider()
    assert len(menu._options) == 2
    assert menu._options[0].key == "1"
    assert menu._options[1].is_divider is True

    # Protocol runtime checkable tests
    class DummyConsole:
        def print(self, *args, **kwargs): pass
        def clear(self): pass

    assert isinstance(DummyConsole(), IConsoleProvider)


# ---------------------------------------------------------------------------
# Test 4: Exception Hierarchy & Forensics
# ---------------------------------------------------------------------------

def test_exception_hierarchy():
    """Verify structured exceptions, error codes, context chaining, and serialization."""
    from interface.exceptions import (
        BalanceFetchError,
        CodeExtractionError,
        ConfigValidationError,
        ConfigurationError,
        ExportError,
        HistoryLedgerError,
        InputError,
        InputTimeoutError,
        InterfaceError,
        KeybindingError,
        LayoutError,
        LedgerCorruptionError,
        MenuError,
        MenuExecutionError,
        PreferencePersistenceError,
        QuickEditError,
        RenderingError,
        SwarmInterfaceError,
        TelemetryError,
        TerminalError,
        ThemeError,
        ThemeNotFoundError,
        TUIError,
    )
    from interface.types import ErrorSeverity

    err = InterfaceError(
        message="Test failure",
        context={"user": "test_user"},
        error_code="ERR_TEST_001",
        component="test_subsystem",
        suggested_action="Check parameters.",
        severity=ErrorSeverity.ERROR,
    )

    assert err.error_code == "ERR_TEST_001"
    assert err.severity == ErrorSeverity.ERROR
    assert err.timestamp > 0

    # Context chaining
    err.chain_context(retry_count=3, node_id="node_a")
    assert err.context["retry_count"] == 3
    assert err.context["node_id"] == "node_a"

    # Serialization
    d = err.to_dict()
    assert d["error_code"] == "ERR_TEST_001"
    assert d["context"]["user"] == "test_user"

    j = err.to_json()
    parsed = json.loads(j)
    assert parsed["component"] == "test_subsystem"

    # from_exception factory
    try:
        raise ValueError("Invalid integer value")
    except ValueError as exc:
        wrapped = InterfaceError.from_exception(exc, component="test_wrapper")
        assert "ValueError" in wrapped.context["original_type"]
        assert wrapped.component == "test_wrapper"

    # Inheritance tests
    assert issubclass(ThemeNotFoundError, ThemeError)
    assert issubclass(ConfigValidationError, ConfigurationError)
    assert issubclass(MenuExecutionError, MenuError)
    assert issubclass(BalanceFetchError, TelemetryError)


# ---------------------------------------------------------------------------
# Test 5: Dynamic Component Registries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_component_registries():
    """Verify thread-safe registration, lookup, and dispatching in MenuRegistry and ThemeRegistry."""
    from interface.registry import (
        InterfaceRegistry,
        MenuRegistry,
        TelemetryRegistry,
        ThemeRegistry,
        TUIAppRegistry,
    )
    from interface.types import ThemePalette

    # 1. Menu Registry Decorator & Dispatch
    @MenuRegistry.register("test_dummy_menu", title="Test Dummy", category="Testing")
    async def dummy_handler(val: str = "ok"):
        return f"result_{val}"

    assert MenuRegistry.get_handler("test_dummy_menu") is not None
    meta = MenuRegistry.get_metadata("test_dummy_menu")
    assert meta is not None
    assert meta.title == "Test Dummy"

    res = await MenuRegistry.dispatch("test_dummy_menu", val="custom")
    assert res == "result_custom"

    # 2. Theme Registry
    ThemeRegistry.register_theme(ThemePalette(name="cyber_synth", primary="bright_magenta", border_style="bright_magenta"))
    synth = ThemeRegistry.get_theme("cyber_synth")
    assert synth is not None
    assert synth.name == "cyber_synth"

    # 3. Telemetry Registry
    @TelemetryRegistry.register_collector("mock_gpu")
    def mock_gpu_collector():
        return {"vram_used_mb": 4096, "utilization_pct": 78}

    assert TelemetryRegistry.get_collector("mock_gpu") is not None
    all_metrics = TelemetryRegistry.collect_all()
    assert "mock_gpu" in all_metrics
    assert all_metrics["mock_gpu"]["vram_used_mb"] == 4096

    # 4. InterfaceRegistry Facade
    assert InterfaceRegistry.menus is MenuRegistry
    assert InterfaceRegistry.themes is ThemeRegistry


# ---------------------------------------------------------------------------
# Test 6: Fluent Builders & Component Factories
# ---------------------------------------------------------------------------

def test_builders_and_factories():
    """Verify MenuBuilder, HeaderBuilder, DashboardLayoutBuilder, and factory instantiators."""
    from interface.builder import (
        DashboardLayoutBuilder,
        HeaderBuilder,
        MenuBuilder,
        TUIAppBuilder,
    )
    from interface.factory import (
        create_interface,
        create_menu,
        create_telemetry_provider,
        create_theme_engine,
        create_tui_app,
    )
    from interface.types import SessionTelemetry

    # MenuBuilder
    builder = (
        MenuBuilder(title="Custom Subsystem")
        .set_category("Testing")
        .set_border_style("cyan")
        .add_item("1", "Status", "View system status", handler=lambda: "status_ok", badge="ONLINE")
        .add_divider()
        .add_item("0", "Exit", "Return to main menu")
    )
    table = builder.build_table()
    assert table is not None
    opts = builder.build_options_dict()
    assert "1" in opts
    assert "0" in opts

    # HeaderBuilder
    telemetry = SessionTelemetry(load=12.5, mem=16.0, active_paper_count=66)
    header_builder = (
        HeaderBuilder(title="TruthGPT Sentinel")
        .set_version("v5.9.0-TEST")
        .set_user_name("Tester")
        .set_telemetry(telemetry)
        .add_update("Neural Engine Active")
        .add_update("Zero Latency Cache Initialized")
    )
    hdr_text = header_builder.build()
    assert hdr_text is not None
    assert "TruthGPT Sentinel" in str(hdr_text)

    # DashboardLayoutBuilder
    layout = (
        DashboardLayoutBuilder()
        .with_header(size=3)
        .with_split_main(left_ratio=2, right_ratio=1)
        .with_footer(size=2)
        .build()
    )
    assert "header" in layout
    assert "main" in layout
    assert "footer" in layout

    # Component Factories
    palette = create_theme_engine("claude")
    assert palette.name == "claude"
    assert palette.primary == "plum1"

    t_provider = create_telemetry_provider()
    assert hasattr(t_provider, "get_system_telemetry")


# ---------------------------------------------------------------------------
# Test 7: Preferences & Persistence
# ---------------------------------------------------------------------------

def test_preferences_manager():
    """Verify configuration loading, default fallback, atomic writing, and corruption recovery."""
    from interface.config import (
        CONFIG_PATH,
        DEFAULT_USER_PREFS,
        PreferenceManager,
        load_user_prefs,
        save_user_prefs,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_cfg = Path(tmp_dir) / "test_prefs.json"

        # 1. Load from non-existent file -> default preferences
        prefs = load_user_prefs(temp_cfg)
        assert prefs["user_name"] == "Explorer"
        assert prefs["theme"] == "claude"
        assert "api_keys" in prefs

        # 2. Modify and Save
        prefs["user_name"] = "NovaArchitect"
        prefs["api_keys"]["deepseek"] = "sk-test-deepseek-12345"
        save_user_prefs(prefs, temp_cfg)

        assert temp_cfg.exists()
        reloaded = load_user_prefs(temp_cfg)
        assert reloaded["user_name"] == "NovaArchitect"
        assert reloaded["api_keys"]["deepseek"] == "sk-test-deepseek-12345"

        # 3. PreferenceManager class
        mgr = PreferenceManager(config_path=temp_cfg)
        assert mgr.get("user_name") == "NovaArchitect"
        mgr.set("theme", "matrix")
        assert mgr.get("theme") == "matrix"

        # 4. Corruption recovery test
        temp_cfg.write_text("INVALID_JSON_CORRUPTED_DATA{{{", encoding="utf-8")
        recovered = load_user_prefs(temp_cfg)
        assert recovered["user_name"] == "Explorer"
        assert (Path(tmp_dir) / "test_prefs.corrupt").exists()


# ---------------------------------------------------------------------------
# Test 8: Telemetry & Live Budget Stats
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_telemetry_provider():
    """Verify telemetry collection and non-blocking background fetching."""
    from interface.telemetry import (
        TelemetryProvider,
        _fast_count_papers,
        fetch_balances_background,
        get_real_budget_stats,
        get_system_telemetry,
    )

    telemetry = get_system_telemetry()
    assert telemetry.load >= 0.0
    assert telemetry.mem >= 0.0
    assert telemetry.session_id.startswith("S-")

    stats = get_real_budget_stats()
    assert "total_usd" in stats
    assert "savings_usd" in stats

    papers = _fast_count_papers()
    assert papers >= 0

    # Non-blocking balance fetcher invocation
    await fetch_balances_background()


# ---------------------------------------------------------------------------
# Test 9: Code Extraction & Export Utilities
# ---------------------------------------------------------------------------

def test_export_and_code_extraction():
    """Verify markdown code extraction across multiple languages and file persistence."""
    from interface.export_utils import (
        LANGUAGE_EXTENSION_MAP,
        export_mission_result,
        extract_and_save_code_blocks,
        extract_target_directory,
        save_mission_output,
    )

    markdown_sample = """# Mission Plan
Here is the implementation in Python:
```python
def solve_problem():
    return 42
```

And in Rust:
```rust
fn solve_problem() -> u32 {
    42
}
```
"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir) / "extracted_src"
        extracted_files = extract_and_save_code_blocks(markdown_sample, target_dir=out_dir, prefix="test_solve")
        assert len(extracted_files) == 2

        py_files = [f for f in extracted_files if f.suffix == ".py"]
        rs_files = [f for f in extracted_files if f.suffix == ".rs"]
        assert len(py_files) == 1
        assert len(rs_files) == 1

        assert "solve_problem" in py_files[0].read_text(encoding="utf-8")
        assert "fn solve_problem" in rs_files[0].read_text(encoding="utf-8")

        # Target directory extraction from prompt
        extracted_dir = extract_target_directory(f"Please output code to {tmp_dir}")
        assert extracted_dir is not None


# ---------------------------------------------------------------------------
# Test 10: Claude Code Aesthetic Style Primitives
# ---------------------------------------------------------------------------

def test_cc_style_primitives():
    """Verify Claude Code styling helpers, glyphs, and spinners."""
    from interface.cc_style import (
        ARROW,
        BULLET,
        CONT,
        CTX_GLYPH,
        SPIN_FRAMES,
        cc_action,
        cc_divider,
        cc_log_activity,
        cc_log_event,
        cc_menu,
        cc_result,
        cc_spinner,
        cc_step,
        expand_pending,
    )

    assert BULLET in ("●", "*")
    assert CONT in ("⎿", "\\_")

    # Spinner context manager test
    with cc_spinner("Compiling Test Kernels") as sp:
        sp.add_tokens(150)
        assert sp._tokens == 150

    # Styling decorators test
    @cc_menu("Diagnostic Unit")
    async def dummy_cc_menu():
        return "menu_rendered"

    assert asyncio.iscoroutinefunction(dummy_cc_menu)


# ---------------------------------------------------------------------------
# Test 11: Interactive TUI Apps & Menus Instantiation
# ---------------------------------------------------------------------------

def test_tui_apps_instantiation():
    """Verify InteractiveDashboardApp, InteractiveSwarmApp, and ModelMenuApp instantiate cleanly."""
    from interface.interactive_dashboard import InteractiveDashboardApp
    from interface.interactive_swarm import InteractiveSwarmApp
    from interface.model_menu import ModelMenuApp
    from interface.modern_claude_ui import ModernTruthGPTInterface
    from interface.swarm_menu import SwarmMenuApp

    # InteractiveDashboardApp
    dash_app = InteractiveDashboardApp(extended=True)
    assert dash_app is not None
    assert hasattr(dash_app, "get_layout")

    # SwarmMenuApp
    mock_agent = MagicMock()
    mock_agent.name = "Architect"
    mock_agent.role = "Lead System Architect"
    swarm_app = SwarmMenuApp(active_agents=[mock_agent])
    assert swarm_app is not None
    assert len(swarm_app.active_agents) == 1

    # InteractiveSwarmApp
    i_swarm_app = InteractiveSwarmApp(active_agents=[mock_agent])
    assert i_swarm_app is not None

    # ModelMenuApp
    model_app = ModelMenuApp()
    assert model_app is not None

    # ModernTruthGPTInterface
    modern_ui = ModernTruthGPTInterface()
    assert modern_ui is not None
    assert modern_ui.system_status["model"] == "TruthGPT"
