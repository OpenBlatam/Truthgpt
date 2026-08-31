"""
TruthGPT Interface Subsystem (System 5.9 Gold Standard).
=========================================================
Unified, modular, enterprise-grade interface package providing:
  - Strongly-typed Domain Schemas, Enums, and Telemetry dataclasses
  - Abstract Interfaces and Protocols enforcing architectural decoupling
  - Domain Exception Hierarchy with forensics, context chaining, and severity tags
  - Thread-Safe Dynamic Component Registries for Menus, Themes, Telemetry, and TUIs
  - Fluent Builders for Menus, Headers, and prompt_toolkit Applications
  - Clean Claude Code / Sentient Cyber-Industrial Terminal Styling (Rich + ANSI)
  - Modular Swarm Orchestration, Missions, Inspectors, and Code Block Extraction
  - Complete Cross-Module Aliasing (optimization_core.interface <-> interface)
"""
from __future__ import annotations

import sys

__version__ = "5.9.0"

# Module Aliasing for seamless dual imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface":
        sys.modules["interface"] = _mod
    elif __name__ == "interface":
        sys.modules["optimization_core.interface"] = _mod

# 1. Config & Persistence
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

# 2. Console & Terminal Subsystem
from .console import (
    LazyConsole,
    clear_screen,
    console,
    disable_quick_edit,
    get_console,
    wait_for_user,
)

# 3. Telemetry & Live Metrics
from .telemetry import (
    _CACHED_PAPER_COUNT,
    _LAST_PAPER_SCAN,
    TelemetryProvider,
    _fast_count_papers,
    fetch_balances_background,
    get_real_budget_stats,
    get_system_telemetry,
)

# 4. State & Event Ledger
from .state import (
    BLOCKCHAIN_READY,
    SYSTEM_LOGS,
    background_missions,
    claude_log_event,
    log_activity,
    log_event,
    system_history,
)

# 5. Theming & Banners
from .theming import (
    get_claude_header,
    get_header,
    get_theme_color,
    get_theme_panel,
    linux_boot_sequence,
)

# 6. Input & Dialog Utilities
from .input_utils import (
    _HAS_PROMPT_TOOLKIT,
    _build_ctrl_o_keybindings,
    _check_prompt_toolkit,
    get_choice,
    get_input,
)

# 7. Export & Code Extraction Utilities
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
    CCSpinner,
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
    get_menu_info,
    get_theme_palette,
    list_available_menus,
    list_available_themes,
    register_menu,
)

# 12. Typed Contracts, Enums & Schemas
from .types import (
    APIBalanceInfo,
    ApiBalanceInfo,
    ComponentStatus,
    EnsembleMode,
    ErrorSeverity,
    EventKind,
    ExportResult,
    InterfaceMode,
    LogLevel,
    MenuAction,
    MenuCategory,
    MenuItem,
    MenuOption,
    MenuState,
    PromptChoice,
    SessionState,
    SessionTelemetry,
    TelemetrySnapshot,
    ThemeConfig,
    ThemePalette,
    ThemeType,
    TUIConfiguration,
    UserPreferences,
    UserPreferencesData,
)

# 13. Interfaces & PEP 544 Protocols
from .interfaces import (
    BaseExportHandler,
    BaseExportManager,
    BaseHistoryLedger,
    BaseInputHandler,
    BaseInputReader,
    BaseInterfaceView,
    BaseMenu,
    BasePreferenceManager,
    BaseSwarmFusionHandler,
    BaseSwarmInspectorHandler,
    BaseSwarmMissionHandler,
    BaseTelemetryCollector,
    BaseTelemetryProvider,
    BaseThemeEngine,
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

# 14. Domain Exception Hierarchy
from .exceptions import (
    BalanceFetchError,
    CodeExtractionError,
    ConfigError,
    ConfigLoadError,
    ConfigSaveError,
    ConfigValidationError,
    ConfigurationError,
    CorruptedConfigError,
    DuplicateMenuError,
    ExportError,
    HistoryLedgerError,
    InputCancelledError,
    InputError,
    InputTimeoutError,
    InterfaceError,
    InvalidInputFormatError,
    InvalidMenuChoiceError,
    InvalidThemeConfigurationError,
    KeybindingError,
    LayoutError,
    LayoutRenderError,
    LedgerCorruptionError,
    MenuDispatchError,
    MenuError,
    MenuExecutionError,
    MenuNotFoundError,
    MetricsCollectionError,
    PreferencePersistenceError,
    QuickEditError,
    RenderingError,
    SwarmInterfaceError,
    TelemetryError,
    TerminalError,
    ThemeError,
    ThemeNotFoundError,
    TUIError,
    TUIExecutionError,
    WidgetInitializationError,
)

# 15. Interactive TUI Apps & Styling
from .tui_base import BaseTUIApp
from .cc_style import (
    CCSpinner,
    cc_action,
    cc_agent_done,
    cc_code_change,
    cc_divider,
    cc_engine_call,
    cc_file_list,
    cc_log_activity,
    cc_log_event,
    cc_menu,
    cc_prompt_footer,
    cc_result,
    cc_searched,
    cc_spinner,
    cc_step,
    cc_tip,
    cc_tool_call,
    cc_tool_output,
    expand_pending,
    has_pending_expansion,
)
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
    "__version__",
    # Config
    "CONFIG_PATH",
    "DEFAULT_USER_PREFS",
    "KEY_MAPPING",
    "USER_PREFS",
    "current_dir",
    "load_user_prefs",
    "save_user_prefs",
    "_invalidate_llm_client_cache",
    # Console
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
    # State & Events
    "BLOCKCHAIN_READY",
    "SYSTEM_LOGS",
    "background_missions",
    "claude_log_event",
    "log_activity",
    "log_event",
    "system_history",
    # Theming
    "get_claude_header",
    "get_header",
    "get_theme_color",
    "get_theme_panel",
    "linux_boot_sequence",
    # Input
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
    "CCSpinner",
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
    "DashboardBuilder",
    "MenuLayoutBuilder",
    "InterfaceBuilder",
    "create_interface_builder",
    "create_tui_builder",
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
    "get_menu_info",
    "get_theme_palette",
    "list_available_menus",
    "list_available_themes",
    "register_menu",
    # Types & Schemas
    "InterfaceMode",
    "ThemeType",
    "EnsembleMode",
    "ErrorSeverity",
    "MenuAction",
    "MenuCategory",
    "LogLevel",
    "EventKind",
    "ComponentStatus",
    "MenuItem",
    "MenuOption",
    "MenuState",
    "SessionState",
    "APIBalanceInfo",
    "ApiBalanceInfo",
    "TelemetrySnapshot",
    "SessionTelemetry",
    "ThemePalette",
    "ThemeConfig",
    "ExportResult",
    "PromptChoice",
    "TUIConfiguration",
    "UserPreferences",
    "UserPreferencesData",
    # Interfaces
    "IConsoleProvider",
    "IConsoleManager",
    "ITelemetryProvider",
    "IThemingProvider",
    "IThemeRenderer",
    "IMenuHandler",
    "ITUIApp",
    "IPreferenceManager",
    "IExportManager",
    "IHistoryLedger",
    "BaseInterfaceView",
    "BaseMenu",
    "BaseTUIComponent",
    "BaseTUIAppInterface",
    "BaseTelemetryCollector",
    "BaseTelemetryProvider",
    "BaseThemeRenderer",
    "BaseThemeEngine",
    "BasePreferenceManager",
    "BaseHistoryLedger",
    "BaseExportHandler",
    "BaseExportManager",
    "BaseInputHandler",
    "BaseDialogHandler",
    "BaseInputReader",
    "BaseSwarmFusionHandler",
    "BaseSwarmInspectorHandler",
    "BaseSwarmMissionHandler",
    # Exceptions
    "InterfaceError",
    "ConfigError",
    "ConfigurationError",
    "ConfigLoadError",
    "ConfigSaveError",
    "PreferencePersistenceError",
    "ConfigValidationError",
    "CorruptedConfigError",
    "TerminalError",
    "QuickEditError",
    "RenderingError",
    "TelemetryError",
    "BalanceFetchError",
    "MetricsCollectionError",
    "TUIError",
    "TUIExecutionError",
    "LayoutError",
    "LayoutRenderError",
    "KeybindingError",
    "WidgetInitializationError",
    "MenuError",
    "MenuNotFoundError",
    "InvalidMenuChoiceError",
    "MenuExecutionError",
    "MenuDispatchError",
    "DuplicateMenuError",
    "ThemeError",
    "ThemeNotFoundError",
    "InvalidThemeConfigurationError",
    "InputError",
    "InputCancelledError",
    "InputTimeoutError",
    "InvalidInputFormatError",
    "ExportError",
    "CodeExtractionError",
    "SwarmInterfaceError",
    "HistoryLedgerError",
    "LedgerCorruptionError",
    # Interactive Apps & Styling
    "BaseTUIApp",
    "CCSpinner",
    "cc_action",
    "cc_agent_done",
    "cc_code_change",
    "cc_divider",
    "cc_engine_call",
    "cc_file_list",
    "cc_log_activity",
    "cc_log_event",
    "cc_menu",
    "cc_prompt_footer",
    "cc_result",
    "cc_searched",
    "cc_spinner",
    "cc_step",
    "cc_tip",
    "cc_tool_call",
    "cc_tool_output",
    "expand_pending",
    "has_pending_expansion",
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
