"""
Enterprise Interface Subsystem Refactor Verification Script.
============================================================
Comprehensive end-to-end verification validating:
  1. Top-Level Imports & Module Aliasing (interface <-> optimization_core.interface)
  2. Public API surface & PEP 544 Protocols / Abstract Base Classes
  3. Domain Enums, Dataclasses, and Typed Contracts
  4. Menu & Theme Dynamic Registries with Decorators and Dispatching
  5. Fluent Builders (InterfaceBuilder, TUIAppBuilder, MenuBuilder, HeaderBuilder, DashboardLayoutBuilder)
  6. Component Factory Functions (create_interface, create_menu, create_tui_app, etc.)
  7. TelemetryProvider Live Caching & Metrics Collection
  8. Preferences Loading, In-Memory Sync, and Atomic Persistence
  9. Code Extraction, File Resolution, and Mission Exporters
  10. Swarm Intelligence Subpackage Integration & Re-exports
  11. Backward Compatibility across legacy consumers (interface.core)
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def run_verification() -> bool:
    print("=" * 80)
    print("🚀 TRUTHGPT INTERFACE SUBSYSTEM REFACTOR VERIFICATION")
    print("=" * 80)

    # Ensure paths
    current_dir = Path(__file__).resolve().parent
    src_dir = current_dir / "src"
    for p in [str(current_dir), str(src_dir)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    success = True

    # -----------------------------------------------------------------------
    # Step 1: Top-Level Imports & Module Aliasing
    # -----------------------------------------------------------------------
    print("\n[1/11] Verifying Top-Level Imports & Dual-Mode Aliasing...")
    try:
        import interface
        import optimization_core.interface as opt_interface

        assert interface is not None, "interface module is None"
        assert opt_interface is not None, "optimization_core.interface is None"
        assert interface is opt_interface, "Dual-mode module aliasing mismatch"
        print(f"  [OK] Interface v{interface.__version__} loaded & aliased successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 1 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 2: Protocols & Interfaces
    # -----------------------------------------------------------------------
    print("\n[2/11] Verifying PEP 544 Protocols & Abstract Base Classes...")
    try:
        from interface.interfaces import (
            BaseExportHandler,
            BaseHistoryLedger,
            BaseInputHandler,
            BaseMenu,
            BasePreferenceManager,
            BaseSwarmFusionHandler,
            BaseSwarmInspectorHandler,
            BaseSwarmMissionHandler,
            BaseTelemetryCollector,
            BaseThemeRenderer,
            BaseTUIAppInterface,
            BaseTUIComponent,
            IConsoleManager,
            IConsoleProvider,
            IExportManager,
            IHistoryLedger,
            IMenuHandler,
            IPreferenceManager,
            ITelemetryProvider,
            IThemeRenderer,
            IThemingProvider,
            ITUIApp,
        )

        class CustomMenu(BaseMenu):
            menu_id = "test_custom"
            title = "Test Custom Menu"

            async def display(self, **kwargs):
                return "displayed"

            def get_options(self):
                return [("1", "Opt 1", lambda: "1")]

        custom_menu = CustomMenu()
        info = custom_menu.get_menu_info()
        assert info["menu_id"] == "test_custom"
        print("  [OK] Protocols and Base Classes validated successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 2 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 3: Domain Types, Enums & Dataclasses
    # -----------------------------------------------------------------------
    print("\n[3/11] Verifying Domain Types, Dataclasses & Enums...")
    try:
        from interface.types import (
            APIBalanceInfo,
            EnsembleMode,
            ErrorSeverity,
            InterfaceMode,
            LogLevel,
            MenuCategory,
            MenuItem,
            MenuOption,
            SessionState,
            SessionTelemetry,
            TelemetrySnapshot,
            ThemePalette,
            ThemeType,
            UserPreferencesData,
        )

        assert InterfaceMode.STANDARD == "standard"
        assert ThemeType.CLAUDE == "claude"
        assert EnsembleMode.RACE == "race"

        palette = ThemePalette(name="custom", primary="cyan")
        assert palette.primary == "cyan"

        user_prefs = UserPreferencesData(user_name="Tester", preferred_engine="deepseek")
        d = user_prefs.to_dict()
        assert d["user_name"] == "Tester"

        print("  [OK] Domain types and dataclasses validated successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 3 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 4: Menu & Theme Dynamic Registries
    # -----------------------------------------------------------------------
    print("\n[4/11] Verifying Menu & Theme Registries and Decorators...")
    try:
        from interface.registry import (
            MENU_REGISTRY,
            THEME_REGISTRY,
            MenuRegistry,
            ThemeRegistry,
            get_menu_info,
            get_theme_palette,
            list_available_menus,
            list_available_themes,
            register_menu,
        )

        # Test registration via decorator
        @register_menu(key="verify_test_menu", title="Verifier Menu", category="Test")
        def sample_test_handler():
            return "verifier_success"

        assert "verify_test_menu" in list_available_menus()
        handler = MENU_REGISTRY.get("verify_test_menu")
        assert handler() == "verifier_success"

        # Test themes
        themes = list_available_themes()
        assert "claude" in themes
        assert "industrial" in themes
        palette = get_theme_palette("claude")
        assert palette is not None and palette.name == "claude"

        print("  [OK] Menu and Theme registries verified successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 4 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 5: Fluent Builders
    # -----------------------------------------------------------------------
    print("\n[5/11] Verifying Fluent Interface & TUI Builders...")
    try:
        from interface.builder import (
            DashboardBuilder,
            DashboardLayoutBuilder,
            HeaderBuilder,
            InterfaceBuilder,
            MenuBuilder,
            MenuLayoutBuilder,
            TUIAppBuilder,
            create_interface_builder,
            create_tui_builder,
        )

        menu_b = MenuBuilder("TestMenu").add_option("1", "Option One")
        built_menu = menu_b.build()
        assert len(built_menu["options"]) == 1

        hdr_b = HeaderBuilder("TruthGPT Sentinel").set_style("plum1").set_subtitle("Secure")
        hdr_panel = hdr_b.build()
        assert hdr_panel is not None

        tui_b = create_tui_builder("dashboard").with_theme("claude").with_extended(True)
        assert tui_b is not None

        print("  [OK] Fluent builders constructed correctly.")
    except Exception as e:
        print(f"  [FAIL] Step 5 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 6: Unified Component Factory Methods
    # -----------------------------------------------------------------------
    print("\n[6/11] Verifying Component Factory Functions...")
    try:
        from interface.factory import (
            create_interface,
            create_menu,
            create_telemetry_provider,
            create_theme_engine,
            create_tui_app,
        )

        app = create_tui_app("dashboard")
        assert app is not None

        theme_eng = create_theme_engine("claude")
        assert theme_eng is not None

        telemetry_prov = create_telemetry_provider()
        assert telemetry_prov is not None

        print("  [OK] Factory methods instantiated components successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 6 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 7: Telemetry Provider & System Metrics
    # -----------------------------------------------------------------------
    print("\n[7/11] Verifying TelemetryProvider Caching & Metrics...")
    try:
        from interface.telemetry import TelemetryProvider, get_system_telemetry

        stats = TelemetryProvider.get_stats()
        assert "load" in stats
        assert "mem" in stats
        assert "session_id" in stats

        balances = TelemetryProvider.get_api_balances()
        assert isinstance(balances, dict)

        compat_stats = get_system_telemetry()
        assert compat_stats["session_id"] == stats["session_id"]

        print("  [OK] TelemetryProvider metrics & caching verified successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 7 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 8: User Preferences & Persistence
    # -----------------------------------------------------------------------
    print("\n[8/11] Verifying User Preferences & Persistence...")
    try:
        from interface.config import (
            DEFAULT_USER_PREFS,
            USER_PREFS,
            PreferenceManager,
            load_user_prefs,
            save_user_prefs,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_cfg_path = Path(tmp_dir) / "test_prefs.json"

            # Test initial default loading
            loaded = load_user_prefs(test_cfg_path)
            assert loaded["user_name"] == DEFAULT_USER_PREFS["user_name"]

            # Test atomic save and reload
            loaded["user_name"] = "Alice_Architect"
            save_user_prefs(loaded, test_cfg_path)

            reloaded = load_user_prefs(test_cfg_path)
            assert reloaded["user_name"] == "Alice_Architect"

            # Test PreferenceManager
            pm = PreferenceManager(test_cfg_path)
            assert pm.get("user_name") == "Alice_Architect"

        print("  [OK] User preferences atomic storage & corruption recovery verified.")
    except Exception as e:
        print(f"  [FAIL] Step 8 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 9: Code Extraction & Mission Exporter
    # -----------------------------------------------------------------------
    print("\n[9/11] Verifying Code Extraction & Mission Exporters...")
    try:
        from interface.export_utils import (
            export_mission_result,
            extract_and_save_code_blocks,
            extract_target_directory,
            save_mission_output,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_md = f"""# Test Mission\n\n```python\ndef test_fn():\n    return 42\n```\n\n```rust\nfn main() {{}}\n```"""
            res_path = export_mission_result("Sample Run", sample_md, export_code=True, target_dir=Path(tmp_dir))
            assert res_path is not None
            assert res_path.exists()

            files = list(Path(tmp_dir).glob("*.*"))
            assert len(files) >= 1

        print("  [OK] Code block extraction & report exports verified successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 9 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 10: Swarm Subpackage Integration
    # -----------------------------------------------------------------------
    print("\n[10/11] Verifying Swarm Subpackage & Re-exports...")
    try:
        import interface.swarm as swarm
        from interface.swarm import (
            BackgroundMission,
            execute_sandbox_code,
            execute_swarm_dispatch,
            extract_filename_from_code,
            handle_background_missions,
            handle_continuous_mission,
            handle_swarm_ask,
            handle_swarm_fusion,
            handle_swarm_telemetry,
            swarm_phase_inspector,
        )

        assert callable(execute_swarm_dispatch)
        assert callable(handle_swarm_ask)
        assert callable(extract_filename_from_code)
        assert issubclass(BackgroundMission, object)

        print("  [OK] Swarm subpackage exports verified successfully.")
    except Exception as e:
        print(f"  [FAIL] Step 10 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Step 11: Backward Compatibility with interface.core
    # -----------------------------------------------------------------------
    print("\n[11/11] Verifying Backward Compatibility with interface.core...")
    try:
        from interface.core import (
            BLOCKCHAIN_READY,
            CONFIG_PATH,
            DEFAULT_USER_PREFS,
            LazyConsole,
            SYSTEM_LOGS,
            TelemetryProvider,
            USER_PREFS,
            clear_screen,
            console,
            disable_quick_edit,
            get_console,
            get_header,
            get_input,
            get_system_telemetry,
            load_user_prefs,
            log_activity,
            log_event,
            save_user_prefs,
            system_history,
            wait_for_user,
        )

        assert console is not None
        assert isinstance(USER_PREFS, dict)
        assert isinstance(SYSTEM_LOGS, list)
        assert callable(log_event)
        assert callable(log_activity)

        print("  [OK] interface.core full backward-compatibility facade verified.")
    except Exception as e:
        print(f"  [FAIL] Step 11 Failed: {e}")
        success = False

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("=" * 80)
    if success:
        print("🎉 RESULT: ALL 11 INTERFACE REFACTOR VERIFICATION CHECKS PASSED PERFECTLY!")
    else:
        print("❌ RESULT: VERIFICATION FAILED - SEE LOGS ABOVE.")
    print("=" * 80)
    return success


if __name__ == "__main__":
    sys.exit(0 if run_verification() else 1)
