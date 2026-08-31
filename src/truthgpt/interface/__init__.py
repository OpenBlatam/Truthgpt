"""
TruthGPT Interface Subsystem — Enterprise Modular Terminal User Interface & Orchestration Hub.
==============================================================================================
Provides:
  - Strongly-typed Domain Schemas, Enums, and Telemetry dataclasses (.types)
  - Abstract Interfaces and Protocols enforcing architectural decoupling (.interfaces)
  - Domain Exception Hierarchy with forensics, context chaining, and severity tags (.exceptions)
  - Thread-Safe Dynamic Component Registries for Menus, Themes, Telemetry, and TUIs (.registry)
  - Fluent Builders and Component Factories for Menus, Headers, and prompt_toolkit Applications (.builder, .factory)
  - Core Preferences, Configuration, and Environment synchronization (.config)
  - High-performance Rich Console proxy and Windows QuickEdit terminal controllers (.console)
  - Non-blocking real-time system metrics, CPU/memory telemetry, and live API cost tracking (.telemetry)
  - Global system event ledger and persistent cross-session activity history (.state, .history_menu)
  - Adaptive terminal theming engines, Claude Code aesthetics, and responsive HUD banners (.theming, .cc_style)
  - Mouse and keyboard input management with prompt_toolkit integration (.input_utils, .tui_base)
  - Multi-language source code extraction and mission markdown persistence (.export_utils)
  - Clean Claude Code / Sentient Cyber-Industrial Terminal Styling (Rich + ANSI) (.cc_style)
  - Modular Swarm Orchestration, Missions, Inspectors, and Code Block Extraction (.swarm, .swarm_menu)
  - Complete Cross-Module Aliasing (optimization_core.interface <-> interface)
"""
from __future__ import annotations

import sys

__version__ = "5.9.0"

# Module Aliasing for Cross-Namespace Backwards Compatibility
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface":
        sys.modules["interface"] = _mod
    elif __name__ == "interface":
        sys.modules["optimization_core.interface"] = _mod

# 1. Config & Preferences
from .config import (
    CONFIG_PATH,
    DEFAULT_USER_PREFS,
    KEY_MAPPING,
    USER_PREFS,
    _invalidate_llm_client_cache,
    current_dir,
    load_user_prefs,
    save_user_prefs,
)

# 2. Console & Terminal Controllers
from .console import (
    LazyConsole,
    clear_screen,
    console,
    disable_quick_edit,
    get_console,
    wait_for_user,
)

# 3. Telemetry & Metrics
from .telemetry import (
    _CACHED_PAPER_COUNT,
    _LAST_PAPER_SCAN,
    TelemetryProvider,
    _fast_count_papers,
    fetch_balances_background,
    get_real_budget_stats,
    get_system_telemetry,
)

# 4. Global State & Logging
from .state import (
    BLOCKCHAIN_READY,
    SYSTEM_LOGS,
    background_missions,
    claude_log_event,
    log_activity,
    log_event,
    system_history,
)

# 5. Theming & Header Renderers
from .theming import (
    get_claude_header,
    get_header,
    get_theme_color,
    get_theme_panel,
    linux_boot_sequence,
)

# 6. User Input & Choice Dialogs
from .input_utils import (
    _HAS_PROMPT_TOOLKIT,
    _build_ctrl_o_keybindings,
    _check_prompt_toolkit,
    get_choice,
    get_input,
)

# 7. Exports & Code Extraction
from .export_utils import (
    LANGUAGE_EXTENSION_MAP,
    export_mission_result,
    extract_and_save_code_blocks,
    extract_target_directory,
    save_mission_output,
)

# 8. Personalization & Dashboard Views
from .personalize import (
    handle_personalize,
    show_main_dashboard,
)

# 9. TUI Base & Claude Code Aesthetic Style
from .tui_base import BaseTUIApp
from .cc_style import (
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
    cc_prompt_footer,
    cc_result,
    cc_spinner,
    cc_step,
    expand_pending,
)

# 10. Declarative Builders & Component Factory
from .builder import (
    DashboardLayoutBuilder,
    HeaderBuilder,
    MenuBuilder,
    TUIAppBuilder,
)
from .factory import (
    create_interface,
    create_menu,
    create_telemetry_provider,
    create_theme_engine,
    create_tui_app,
)

# 11. Registries
from .registry import (
    InterfaceRegistry,
    MENU_REGISTRY,
    MenuRegistry,
    THEME_REGISTRY,
    TelemetryRegistry,
    ThemeRegistry,
    TUIAppRegistry,
)

# 12. Typed Contracts, Enums & Schemas
from .types import (
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
    ThemeType,
    UserPreferences,
)

# 13. Interfaces & PEP 544 Protocols
from .interfaces import (
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
    BaseTUIComponent,
    IConsoleProvider,
    IMenuHandler,
    ITelemetryProvider,
    IThemingProvider,
    ITUIApp,
)

# 14. Domain Exception Hierarchy
from .exceptions import (
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

# 15. Interactive TUI Apps
from .interactive_dashboard import InteractiveDashboardApp
from .interactive_swarm import InteractiveSwarmApp, get_interactive_choice
from .model_menu import ModelMenuApp, model_menu, models_menu
from .modern_claude_ui import ModernTruthGPTInterface

# 16. Menus & Workflow Routers
from .blockchain_menu import blockchain_menu
from .comm_menu import (
    embodied_rl_menu,
    handle_executive_prompt,
    handle_messaging_apps,
    marketing_intelligence_menu,
)
from .evolution_menu import handle_system_evolution
from .history_menu import (
    history_menu,
    load_history,
    persist_current_session,
    record_action,
)
from .infra_menu import (
    infrastructure_menu,
    task_registry_menu,
)
from .overdrive_menu import (
    async_input_with_timeout,
    handle_overdrive_menu,
)
from .research_menu import research_menu
from .swarm_menu import SwarmMenuApp, swarm_menu
from .system_menu import (
    kernel_menu,
    opts_menu,
    system_menu,
)

__all__ = [
    # Metadata
    "__version__",
    # Config & Prefs
    "CONFIG_PATH",
    "DEFAULT_USER_PREFS",
    "KEY_MAPPING",
    "USER_PREFS",
    "current_dir",
    "load_user_prefs",
    "save_user_prefs",
    "_invalidate_llm_client_cache",
    # Console & Terminal
    "LazyConsole",
    "clear_screen",
    "console",
    "disable_quick_edit",
    "get_console",
    "wait_for_user",
    # Telemetry
    "TelemetryProvider",
    "_CACHED_PAPER_COUNT",
    "_LAST_PAPER_SCAN",
    "_fast_count_papers",
    "fetch_balances_background",
    "get_real_budget_stats",
    "get_system_telemetry",
    # State & Logging
    "BLOCKCHAIN_READY",
    "SYSTEM_LOGS",
    "background_missions",
    "claude_log_event",
    "log_activity",
    "log_event",
    "system_history",
    # Theming & Headers
    "get_claude_header",
    "get_header",
    "get_theme_color",
    "get_theme_panel",
    "linux_boot_sequence",
    # Input & Prompts
    "_HAS_PROMPT_TOOLKIT",
    "_build_ctrl_o_keybindings",
    "_check_prompt_toolkit",
    "get_choice",
    "get_input",
    # Exports & Extraction
    "LANGUAGE_EXTENSION_MAP",
    "export_mission_result",
    "extract_and_save_code_blocks",
    "extract_target_directory",
    "save_mission_output",
    # Personalize
    "handle_personalize",
    "show_main_dashboard",
    # TUI Base & Styling
    "BaseTUIApp",
    "cc_menu",
    "cc_step",
    "cc_action",
    "cc_spinner",
    "cc_divider",
    "cc_result",
    "cc_log_event",
    "cc_log_activity",
    "cc_prompt_footer",
    "expand_pending",
    "BULLET",
    "CONT",
    "SPIN_FRAMES",
    "ARROW",
    "CTX_GLYPH",
    # Builders & Factories
    "MenuBuilder",
    "HeaderBuilder",
    "TUIAppBuilder",
    "DashboardLayoutBuilder",
    "create_interface",
    "create_menu",
    "create_telemetry_provider",
    "create_theme_engine",
    "create_tui_app",
    # Registries
    "InterfaceRegistry",
    "MenuRegistry",
    "MENU_REGISTRY",
    "TelemetryRegistry",
    "ThemeRegistry",
    "THEME_REGISTRY",
    "TUIAppRegistry",
    # Types & Schemas
    "ThemeType",
    "EnsembleMode",
    "ErrorSeverity",
    "MenuAction",
    "SessionState",
    "ApiBalanceInfo",
    "SessionTelemetry",
    "ThemeConfig",
    "MenuOption",
    "ExportResult",
    "PromptChoice",
    "UserPreferences",
    # Interfaces
    "IConsoleProvider",
    "ITelemetryProvider",
    "IThemingProvider",
    "IMenuHandler",
    "ITUIApp",
    "BaseMenu",
    "BaseTUIComponent",
    "BaseTelemetryCollector",
    "BaseThemeRenderer",
    "BasePreferenceManager",
    "BaseHistoryLedger",
    "BaseExportHandler",
    "BaseInputHandler",
    "BaseSwarmFusionHandler",
    "BaseSwarmInspectorHandler",
    "BaseSwarmMissionHandler",
    # Exceptions
    "InterfaceError",
    "ConfigurationError",
    "ConfigValidationError",
    "PreferencePersistenceError",
    "TerminalError",
    "QuickEditError",
    "RenderingError",
    "ThemeError",
    "ThemeNotFoundError",
    "TelemetryError",
    "BalanceFetchError",
    "TUIError",
    "LayoutError",
    "KeybindingError",
    "MenuError",
    "MenuExecutionError",
    "InputError",
    "InputTimeoutError",
    "ExportError",
    "CodeExtractionError",
    "SwarmInterfaceError",
    "HistoryLedgerError",
    "LedgerCorruptionError",
    # Interactive Apps
    "InteractiveDashboardApp",
    "InteractiveSwarmApp",
    "get_interactive_choice",
    "SwarmMenuApp",
    "ModelMenuApp",
    "ModernTruthGPTInterface",
    # Menus
    "blockchain_menu",
    "handle_messaging_apps",
    "marketing_intelligence_menu",
    "embodied_rl_menu",
    "handle_executive_prompt",
    "handle_system_evolution",
    "history_menu",
    "load_history",
    "persist_current_session",
    "record_action",
    "infrastructure_menu",
    "task_registry_menu",
    "handle_overdrive_menu",
    "async_input_with_timeout",
    "research_menu",
    "models_menu",
    "model_menu",
    "swarm_menu",
    "system_menu",
    "opts_menu",
    "kernel_menu",
]
