"""
TruthGPT Interface Core Facade.
===============================
Unified access layer re-exporting configuration, terminal controls, telemetry,
headers, prompts, event logs, and reporting engines for 100% backward compatibility.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rich.columns import Columns
from rich.panel import Panel

# ── Re-exports from Submodules ─────────────────────────────────────────

from interface.config import (
    CONFIG_PATH,
    DEFAULT_USER_PREFS,
    USER_PREFS,
    PreferenceManager,
    current_dir,
    load_user_prefs,
    save_user_prefs,
    _invalidate_llm_client_cache,
)
from interface.console import (
    LazyConsole,
    clear_screen,
    console,
    disable_quick_edit,
    get_console,
    wait_for_user,
)
from interface.constants import (
    AVAILABLE_ENGINES,
    CODE_EXTENSION_MAP,
    DEFAULT_API_CREDITS,
    DEFAULT_ENGINE,
    DEFAULT_THEME,
    DEFAULT_USER_NAME,
    ENGINE_METADATA,
    OPENROUTER_MODEL_NAMES,
    OPENROUTER_MODELS,
    THEME_COLORS,
)
from interface.events import (
    BLOCKCHAIN_READY,
    SYSTEM_LOGS,
    background_missions,
    load_history,
    log_activity,
    log_event,
    persist_current_session,
    record_action,
    system_history,
)
from interface.export import (
    export_mission_result,
    extract_and_save_code_blocks,
    extract_target_directory,
    save_mission_output,
)
try:
    from interface.export_utils import LANGUAGE_EXTENSION_MAP
except ImportError:
    LANGUAGE_EXTENSION_MAP = CODE_EXTENSION_MAP
from interface.header import (
    get_claude_header,
    get_header,
    linux_boot_sequence,
)
from interface.personalize import handle_personalize
from interface.prompts import (
    _build_ctrl_o_keybindings,
    _check_prompt_toolkit,
    async_input_with_timeout,
    get_choice,
    get_input,
    get_theme_color,
    get_theme_panel,
)
from interface.telemetry import (
    TelemetryProvider,
    _fast_count_papers,
    fetch_balances_background,
    get_real_budget_stats,
    get_system_telemetry,
)
from interface.types import (
    ActivityLogEntry,
    ApiBalanceInfo,
    EnsembleMode,
    ExportFormat,
    ExportResult,
    HeaderConfig,
    LogLevel,
    MenuItem,
    MenuSection,
    SystemLogEntry,
    SystemStatus,
    TelemetryData,
    ThemeType,
    UserPreferencesDict,
)


# ── Backwards Compatibility Aliases ───────────────────────────────────

def claude_log_event(layer: str, event: str, status: str = "DONE") -> None:
    """Claude-style log entry: clean and minimal."""
    colors = {"DONE": "green", "RUNNING": "cyan", "ERROR": "red", "PENDING": "dim"}
    color = colors.get(status, "white")
    timestamp = time.strftime("%H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] [bold plum1]│[/bold plum1] [white]{layer.upper():<8}[/white] [dim]➔[/dim] [{color}]{event}[/{color}]")


async def show_main_dashboard(extended: bool = False) -> None:
    """Renders the static terminal dashboard fallback."""
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        try:
            from interface.cc_style import cc_action, cc_prompt_footer
            clear_screen()
            console.print(get_header())
            core_layers = [
                ("K", "🛡️ Kernel"), ("1", "🐝 Swarm"), ("2", "🚀 Frontier"), ("3", "🔍 Research")
            ]
            for lid, name in core_layers:
                console.print(f"  [bold orange3]{lid:>2}[/bold orange3]  [white]{name}[/white]")

            if extended:
                console.print()
                cc_action("ADVANCED & EXTERNAL LAYERS", status="INFO")
                advanced_layers = [
                    ("4", "⚙️ Opts"), ("5", "🧠 Labs"), ("6", "📱 Comm"),
                    ("9", "⛓️ Web3"), ("10", "🖥️ Node"), ("11", "📜 Tasks"),
                    ("13", "📊 Market"), ("15", "🤖 RL"), ("16", "⚡ Overdrive"),
                    ("H", "📜 History"), ("P", "👤 Settings"),
                ]
                cols = [f"  [bold cyan]{lid:>2}[/bold cyan] [white]{name}[/white]" for lid, name in advanced_layers]
                console.print(Columns(cols, equal=True, expand=True))
            else:
                console.print("\n [dim] (Type '99' or '+' to toggle Extended View) [/dim]")

            cc_prompt_footer(context_hint="TruthGPT OS v5.9", interrupt_hint="Type command ID")
            return
        except Exception:
            pass

    clear_screen()
    console.print(get_header())

    core_layers = [
        ("K", "🛡️ Kernel"), ("1", "🐝 Swarm"), ("2", "🚀 Frontier"), ("3", "🔍 Research")
    ]
    for lid, name in core_layers:
        console.print(f"  [bold orange3]{lid:>2}[/bold orange3]  [white]{name}[/white]")

    if extended:
        console.print("\n [bold white]ADVANCED & EXTERNAL LAYERS[/bold white]\n")
        advanced_layers = [
            ("4", "⚙️ Opts"), ("5", "🧠 Labs"), ("6", "📱 Comm"),
            ("9", "⛓️ Web3"), ("10", "🖥️ Node"), ("11", "📜 Tasks"),
            ("13", "📊 Market"), ("15", "🤖 RL"), ("16", "⚡ Overdrive"),
            ("H", "📜 History"), ("P", "👤 Settings"),
        ]
        cols = [f"  [bold cyan]{lid:>2}[/bold cyan] [white]{name}[/white]" for lid, name in advanced_layers]
        console.print(Columns(cols, equal=True, expand=True))
    else:
        console.print("\n [dim] (Type '99' or '+' to toggle Extended View) [/dim]")

    console.print("\n [bold white]Type command ID or 'help' to begin.[/bold white]")


__all__ = [
    # Config
    "CONFIG_PATH",
    "DEFAULT_USER_PREFS",
    "USER_PREFS",
    "current_dir",
    "load_user_prefs",
    "save_user_prefs",
    "_invalidate_llm_client_cache",
    "PreferenceManager",
    # Console
    "console",
    "get_console",
    "LazyConsole",
    "disable_quick_edit",
    "clear_screen",
    "wait_for_user",
    # Header & Banners
    "get_header",
    "get_claude_header",
    "linux_boot_sequence",
    # Telemetry
    "TelemetryProvider",
    "get_system_telemetry",
    "get_real_budget_stats",
    "fetch_balances_background",
    "_fast_count_papers",
    # Events & Ledger
    "log_event",
    "log_activity",
    "record_action",
    "persist_current_session",
    "load_history",
    "SYSTEM_LOGS",
    "system_history",
    "background_missions",
    "BLOCKCHAIN_READY",
    "claude_log_event",
    # Prompts & Choice
    "get_input",
    "get_choice",
    "async_input_with_timeout",
    "get_theme_color",
    "get_theme_panel",
    "_build_ctrl_o_keybindings",
    "_check_prompt_toolkit",
    # Export & Reports
    "LANGUAGE_EXTENSION_MAP",
    "export_mission_result",
    "save_mission_output",
    "extract_target_directory",
    "extract_and_save_code_blocks",
    # Personalize
    "handle_personalize",
    "show_main_dashboard",
    # Types
    "ThemeType",
    "EnsembleMode",
    "ExportFormat",
    "LogLevel",
    "SystemStatus",
    "TelemetryData",
    "ApiBalanceInfo",
    "UserPreferencesDict",
    "SystemLogEntry",
    "ActivityLogEntry",
    "MenuItem",
    "MenuSection",
    "ExportResult",
    "HeaderConfig",
]
