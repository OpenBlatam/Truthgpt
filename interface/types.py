"""
Domain Types & Data Models for TruthGPT Interface Module.
=========================================================
Comprehensive type definitions, Enums, TypedDicts, and dataclasses for
terminal layouts, user preferences, telemetry, headers, and menu routing.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from typing_extensions import TypedDict

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.types":
        sys.modules["interface.types"] = _mod
    elif __name__ == "interface.types":
        sys.modules["optimization_core.interface.types"] = _mod


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class InterfaceMode(str, Enum):
    """Execution mode of the interface system."""
    STANDARD = "standard"
    EXTENDED = "extended"
    HEADLESS = "headless"
    TUI_DASHBOARD = "tui_dashboard"
    TUI_SWARM = "tui_swarm"
    MINIMAL = "minimal"


class ThemeType(str, Enum):
    """Supported UI themes for TruthGPT terminal interfaces."""
    INDUSTRIAL = "industrial"
    CLAUDE = "claude"
    MINIMALIST = "minimalist"
    ANTHROPIC = "anthropic"
    MATRIX = "matrix"
    NEON = "neon"
    CYBERPUNK = "cyberpunk"
    DARK = "dark"

    @classmethod
    def from_str(cls, value: str) -> "ThemeType":
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.INDUSTRIAL

    from_string = from_str


class EnsembleMode(str, Enum):
    """Routing & arbitration strategies for multi-engine ensembles."""
    RACE = "race"
    CONSENSUS = "consensus"
    PARALLEL = "parallel"
    MAJORITY = "majority"
    DEBATE = "debate"
    BAYESIAN = "bayesian"

    @classmethod
    def from_str(cls, value: str) -> "EnsembleMode":
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.RACE

    from_string = from_str


class ExportFormat(str, Enum):
    """Supported output formats for reports and research exports."""
    MD = "MD"
    PDF = "PDF"
    WORD = "WORD"
    JSON = "JSON"

    @classmethod
    def from_str(cls, value: str) -> "ExportFormat":
        val = value.upper().strip()
        try:
            return cls(val)
        except ValueError:
            return cls.MD


class MenuAction(str, Enum):
    """Actions performed in menu lifecycle."""
    SELECT = "select"
    BACK = "back"
    REFRESH = "refresh"
    HELP = "help"
    EXIT = "exit"
    TOGGLE_EXTENDED = "toggle_extended"


class MenuCategory(str, Enum):
    """Categorization for registered menus."""
    SYSTEM = "system"
    MODEL = "model"
    SWARM = "swarm"
    INFRASTRUCTURE = "infrastructure"
    RESEARCH = "research"
    EVOLUTION = "evolution"
    COMMUNICATION = "communication"
    BLOCKCHAIN = "blockchain"
    OVERDRIVE = "overdrive"
    HISTORY = "history"
    SETTINGS = "settings"
    CUSTOM = "custom"


class LogLevel(str, Enum):
    """Interface event logging status levels."""
    DONE = "DONE"
    OK = "OK"
    RUNNING = "RUNNING"
    WAIT = "WAIT"
    WARN = "WARN"
    ERROR = "ERROR"
    FAIL = "FAIL"
    INFO = "INFO"


class EventKind(str, Enum):
    """Types of logged system entries."""
    EVENT = "event"
    ACTIVITY = "activity"
    ALERT = "alert"
    DEBUG = "debug"
    METRIC = "metric"


class SystemStatus(str, Enum):
    """System operational readiness status."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    INITIALIZING = "INITIALIZING"
    DEGRADED = "DEGRADED"
    SIMULATED = "SIMULATED"
    READY = "READY"
    SANDBOX_HARDENED = "SANDBOX_HARDENED"


class ComponentStatus(str, Enum):
    """Operational status of submodules and services."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    INITIALIZING = "INITIALIZING"
    DEGRADED = "DEGRADED"
    SIMULATED = "SIMULATED"
    READY = "READY"


class ErrorSeverity(str, Enum):
    """Severity ratings for interface and runtime diagnostics."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# TypedDicts
# ---------------------------------------------------------------------------

class ApiKeyDict(TypedDict, total=False):
    """API keys mapped per reasoning provider."""
    telegram: str
    discord: str
    slack: str
    whatsapp: str
    openai: str
    deepseek: str
    anthropic: str
    google: str
    openrouter: str


class ApiCreditDict(TypedDict, total=False):
    """Starting/offline budget balance estimates in USD."""
    claude: float
    openai: float
    google: float


class UserPreferencesDict(TypedDict, total=False):
    """Serialized user configuration schema."""
    user_name: str
    preferred_engine: str
    theme: str
    continuous_mode: bool
    mcp_servers: List[str]
    api_keys: ApiKeyDict
    api_credits: ApiCreditDict
    ensemble_mode: str
    google_access_token: str
    google_service_account: str
    engine_models: Dict[str, str]
    mcts_optimized: bool
    speculative_decoding: bool
    kv_quantization: bool
    dpo_truth_bias: bool
    rag_fusion_opt: bool
    cove_hallucination_control: bool
    math_formalizer: bool
    sota_injection: bool
    self_refinement: bool
    flash_attention_v3: bool
    dynamic_lora: bool
    forensic_audit: bool
    cross_model_moe: bool
    cache_warming: bool


class SystemLogEntry(TypedDict):
    """Structured record of a single system layer event."""
    time: str
    layer: str
    event: str
    status: str
    session: Optional[str]
    kind: Optional[str]


class ActivityLogEntry(TypedDict):
    """Structured record of an activity in the session ledger."""
    time: str
    module: str
    task: str
    status: str
    date: Optional[str]
    session: Optional[str]
    kind: Optional[str]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ThemePalette:
    """Color palette and token styling definition for a theme."""
    name: str
    primary: str = "cyan"
    secondary: str = "magenta"
    accent: str = "yellow"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    neutral: str = "white"
    dim: str = "dim"
    background: str = "black"
    border_style: str = "cyan"
    focused_color: str = "#00ffff"
    banner_gradient: List[str] = field(default_factory=lambda: ["plum1", "deep_sky_blue1", "green1"])
    custom_tokens: Dict[str, str] = field(default_factory=dict)
    primary_color: str = ""
    secondary_color: str = ""
    accent_color: str = ""
    border_color: str = ""
    is_dark: bool = True

    def __post_init__(self):
        if self.primary_color:
            self.primary = self.primary_color
        else:
            self.primary_color = self.primary

        if self.secondary_color:
            self.secondary = self.secondary_color
        else:
            self.secondary_color = self.secondary

        if self.accent_color:
            self.accent = self.accent_color
        else:
            self.accent_color = self.accent

        if self.border_color:
            self.border_style = self.border_color
        else:
            self.border_color = self.border_style


ThemeConfig = ThemePalette



@dataclass
class MenuItem:
    """Descriptor for an interactive menu item."""
    id: str = ""
    name: str = ""
    key: str = ""
    title: str = ""
    handler: Optional[Callable[..., Any]] = None
    category: Union[MenuCategory, str] = MenuCategory.CUSTOM
    description: str = ""
    shortcut: Optional[str] = None
    icon: str = "🔹"
    is_async: bool = True
    requires_auth: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    badge: Optional[str] = None

    def __post_init__(self):
        if not self.key and self.id:
            self.key = self.id
        elif not self.id and self.key:
            self.id = self.key
        if not self.title and self.name:
            self.title = self.name
        elif not self.name and self.title:
            self.name = self.title


MenuOption = MenuItem


@dataclass
class MenuSection:
    """Group of menu items under a shared header."""
    title: str
    items: List[MenuItem] = field(default_factory=list)
    style: str = "white"


@dataclass
class MenuState:
    """Runtime state container for menu navigation and history."""
    active_menu_id: str = "main"
    selected_index: int = 0
    breadcrumbs: List[str] = field(default_factory=lambda: ["Main"])
    history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


SessionState = MenuState


@dataclass
class APIBalanceInfo:
    """Data container for an AI provider API credit balance or cost estimate."""
    provider: str
    amount: Optional[float] = None
    val: Optional[float] = None
    unit: str = "USD"
    balance_type: str = "API"  # "API Balance", "API Cost", "Est"
    usage: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if self.amount is None and self.val is not None:
            self.amount = self.val
        elif self.val is None and self.amount is not None:
            self.val = self.amount

    def formatted(self) -> str:
        amt = self.amount if self.amount is not None else self.val
        if amt is None:
            return "N/A"
        return f"${amt:.4f}"


ApiBalanceInfo = APIBalanceInfo


@dataclass
class TelemetrySnapshot:
    """System resource metrics and runtime status snapshot."""
    load: float = 0.0
    mem: float = 0.0
    session_id: str = "TRUTH"
    version: str = "TruthGPT v2.4.1"
    timestamp: float = 0.0
    balances: Dict[str, Tuple[Optional[float], str]] = field(default_factory=dict)
    cached_paper_count: int = 66
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "load": self.load,
            "mem": self.mem,
            "session_id": self.session_id,
            "version": self.version,
        }


TelemetryData = TelemetrySnapshot
SessionTelemetry = TelemetrySnapshot


@dataclass
class UserPreferencesData:
    """Strongly typed data structure for user preferences."""
    user_name: str = "Explorer"
    preferred_engine: str = "deepseek"
    theme: str = "claude"
    continuous_mode: bool = False
    mcp_servers: List[str] = field(default_factory=lambda: ["http://localhost:8000"])
    api_keys: Dict[str, str] = field(default_factory=lambda: {
        "telegram": "", "discord": "", "slack": "", "whatsapp": "",
        "openai": "", "deepseek": "", "anthropic": "", "google": "", "openrouter": ""
    })
    api_credits: Dict[str, float] = field(default_factory=lambda: {
        "claude": 10.00, "openai": 10.00, "google": 10.00
    })
    ensemble_mode: str = "race"
    google_access_token: str = ""
    google_service_account: str = ""
    engine_models: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_name": self.user_name,
            "preferred_engine": self.preferred_engine,
            "theme": self.theme,
            "continuous_mode": self.continuous_mode,
            "mcp_servers": list(self.mcp_servers),
            "api_keys": dict(self.api_keys),
            "api_credits": dict(self.api_credits),
            "ensemble_mode": self.ensemble_mode,
            "google_access_token": self.google_access_token,
            "google_service_account": self.google_service_account,
            "engine_models": dict(self.engine_models),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserPreferencesData:
        if not isinstance(data, dict):
            return cls()
        return cls(
            user_name=data.get("user_name", "Explorer"),
            preferred_engine=data.get("preferred_engine", "deepseek"),
            theme=data.get("theme", "claude"),
            continuous_mode=bool(data.get("continuous_mode", False)),
            mcp_servers=data.get("mcp_servers", ["http://localhost:8000"]),
            api_keys=dict(data.get("api_keys", {})),
            api_credits=dict(data.get("api_credits", {})),
            ensemble_mode=data.get("ensemble_mode", "race"),
            google_access_token=data.get("google_access_token", ""),
            google_service_account=data.get("google_service_account", ""),
            engine_models=dict(data.get("engine_models", {})),
        )


UserPreferences = UserPreferencesData


@dataclass
class ExportResult:
    """Result summary of a report/code export operation."""
    success: bool
    target_path: Optional[str] = None
    output_path: Optional[str] = None
    format: ExportFormat = ExportFormat.MD
    code_blocks_extracted: int = 0
    code_blocks_count: int = 0
    extracted_files: List[str] = field(default_factory=list)
    saved_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.output_path and self.target_path:
            self.output_path = self.target_path
        elif not self.target_path and self.output_path:
            self.target_path = self.output_path
        if not self.code_blocks_count and self.code_blocks_extracted:
            self.code_blocks_count = self.code_blocks_extracted
        elif not self.code_blocks_extracted and self.code_blocks_count:
            self.code_blocks_extracted = self.code_blocks_count
        if not self.saved_files and self.extracted_files:
            self.saved_files = self.extracted_files
        elif not self.extracted_files and self.saved_files:
            self.extracted_files = self.saved_files
        if not self.error and self.error_message:
            self.error = self.error_message
        elif not self.error_message and self.error:
            self.error_message = self.error


@dataclass
class HeaderConfig:
    """Configuration options for dynamic terminal headers."""
    theme: ThemeType = ThemeType.INDUSTRIAL
    version: str = "v5.9.0-GOLD"
    user_name: str = "Explorer"
    updates: List[str] = field(default_factory=list)
    show_logo: bool = True
    show_telemetry: bool = True
    compact_mode: bool = False


@dataclass
class PromptChoice:
    """Option descriptor for interactive user prompts."""
    key: str
    label: str
    description: str = ""
    is_default: bool = False


@dataclass
class TUIConfiguration:
    """Configuration settings for prompt_toolkit TUI rendering."""
    refresh_interval: float = 0.5
    mouse_support: bool = True
    full_screen: bool = True
    theme: str = "claude"
    extended_mode: bool = True
    padding: int = 1
    custom_styles: Dict[str, str] = field(default_factory=dict)


__all__ = [
    "InterfaceMode",
    "ThemeType",
    "EnsembleMode",
    "ExportFormat",
    "MenuAction",
    "MenuCategory",
    "LogLevel",
    "EventKind",
    "SystemStatus",
    "ComponentStatus",
    "ErrorSeverity",
    "ApiKeyDict",
    "ApiCreditDict",
    "UserPreferencesDict",
    "SystemLogEntry",
    "ActivityLogEntry",
    "ThemePalette",
    "ThemeConfig",
    "MenuItem",
    "MenuOption",
    "MenuSection",
    "MenuState",
    "SessionState",
    "APIBalanceInfo",
    "ApiBalanceInfo",
    "TelemetrySnapshot",
    "TelemetryData",
    "SessionTelemetry",
    "UserPreferencesData",
    "UserPreferences",
    "ExportResult",
    "HeaderConfig",
    "PromptChoice",
    "TUIConfiguration",
]
