"""
Formal Abstract Base Classes & Protocols for TruthGPT Interface Subsystem.
==========================================================================
Defines the core contracts for views, menus, TUI components,
telemetry providers, theme engines, and dialog handlers.
"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, runtime_checkable

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.interfaces":
        sys.modules["interface.interfaces"] = _mod
    elif __name__ == "interface.interfaces":
        sys.modules["optimization_core.interface.interfaces"] = _mod


# ── Protocols (PEP 544) ───────────────────────────────────────────────────

@runtime_checkable
class IConsoleProvider(Protocol):
    """Protocol for Rich console access and terminal control."""

    def print(self, *args: Any, **kwargs: Any) -> None:
        ...

    def clear(self) -> None:
        ...


IConsoleManager = IConsoleProvider


@runtime_checkable
class ITelemetryProvider(Protocol):
    """Protocol for system load, memory, and API metrics collection."""

    def get_stats(self) -> Dict[str, Any]:
        ...

    def get_api_balances(self) -> Dict[str, Tuple[Optional[float], str]]:
        ...


@runtime_checkable
class IThemingProvider(Protocol):
    """Protocol for theme-specific header, palette, and style generation."""

    def get_header(self, extended: bool = True) -> Any:
        ...

    def get_theme_color(self, name: str) -> str:
        ...


IThemeRenderer = IThemingProvider


@runtime_checkable
class IMenuHandler(Protocol):
    """Protocol for executing interactive menu operations."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


@runtime_checkable
class ITUIApp(Protocol):
    """Protocol for prompt_toolkit TUI application lifecycle."""

    async def run(self) -> Optional[str]:
        ...

    def get_layout(self) -> Any:
        ...


@runtime_checkable
class IPreferenceManager(Protocol):
    """Protocol for user preference management."""

    def load(self) -> Dict[str, Any]:
        ...

    def save(self, prefs: Dict[str, Any]) -> None:
        ...


@runtime_checkable
class IExportManager(Protocol):
    """Protocol for exporting reports and code blocks."""

    def export(self, title: str, content: str, export_code: bool = True) -> Any:
        ...


@runtime_checkable
class IHistoryLedger(Protocol):
    """Protocol for session and event ledger persistence."""

    def record_event(self, entry: Dict[str, Any]) -> None:
        ...

    def load_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        ...


# ── Abstract Base Classes (ABCs) ──────────────────────────────────────────

class BaseInterfaceView(ABC):
    """Abstract base class for all rendered terminal views and canvases."""

    @abstractmethod
    def render(self, **kwargs: Any) -> Any:
        """Render the interface view to console or formatted buffer."""
        pass

    @abstractmethod
    def handle_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        """Process an incoming interface event or state transition."""
        pass


class BaseMenu(ABC):
    """Abstract base class for interactive CLI and TUI menus."""

    menu_id: str = "base_menu"
    title: str = "Base Menu"
    category: str = "general"
    description: str = ""
    shortcut: Optional[str] = None
    icon: str = "📌"

    def __init__(
        self,
        title: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        menu_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.menu_id = menu_id if menu_id is not None else getattr(self.__class__, "menu_id", "base_menu")
        self.title = title if title is not None else getattr(self.__class__, "title", "Base Menu")
        self.category = category if category is not None else getattr(self.__class__, "category", "general")
        self.description = description if description is not None else getattr(self.__class__, "description", "")
        self.shortcut = kwargs.get("shortcut", getattr(self.__class__, "shortcut", None))
        self.icon = kwargs.get("icon", getattr(self.__class__, "icon", "📌"))
        self._options: List[Any] = []

    def add_option(
        self,
        key: str,
        title: str,
        description: str = "",
        handler: Optional[Callable[..., Any]] = None,
        shortcut: Optional[str] = None,
        badge: Optional[str] = None,
    ) -> "BaseMenu":
        from .types import MenuOption
        self._options.append(
            MenuOption(
                key=key,
                title=title,
                description=description,
                handler=handler,
                shortcut=shortcut,
                badge=badge,
            )
        )
        return self

    def add_divider(self) -> "BaseMenu":
        from .types import MenuOption
        self._options.append(
            MenuOption(key="", title="", is_divider=True)
        )
        return self

    def get_options(self) -> List[Any]:
        """Return the list of (key/index, label, handler_callable) options."""
        return list(self._options)

    async def render_and_execute(self, **kwargs: Any) -> Any:
        """Render the menu view and dispatch user selections."""
        return await self.display(**kwargs)

    async def display(self, **kwargs: Any) -> Any:
        """Display the menu to the user and handle user interactions asynchronously."""
        return None

    def get_menu_info(self) -> Dict[str, Any]:
        """Return structured metadata about this menu."""
        return {
            "menu_id": self.menu_id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "shortcut": self.shortcut,
            "icon": self.icon,
        }


class BaseTUIComponent(ABC):
    """Abstract base class for prompt_toolkit / Rich UI components."""

    @abstractmethod
    def get_layout(self) -> Any:
        """Return the layout container for this TUI component."""
        pass

    @abstractmethod
    async def run(self) -> Optional[str]:
        """Execute the TUI component lifecycle and return the user selection/result."""
        pass


class BaseTUIAppInterface(ABC):
    """Abstract base contract for prompt_toolkit full-screen TUI apps."""

    @abstractmethod
    def get_layout(self) -> Any:
        pass

    @abstractmethod
    async def run(self) -> Optional[str]:
        pass


class BaseTelemetryCollector(ABC):
    """Abstract base class for system telemetry and metrics collectors."""

    @classmethod
    @abstractmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Gather and return current system performance metrics."""
        pass

    @classmethod
    @abstractmethod
    def get_api_balances(cls) -> Dict[str, Tuple[Optional[float], str]]:
        """Return cached or refreshed API balances and credit estimates."""
        pass


BaseTelemetryProvider = BaseTelemetryCollector


class BaseThemeRenderer(ABC):
    """Abstract base class for theme schemes, banners, and panel styling."""

    @abstractmethod
    def get_header(self, extended: bool = True) -> Any:
        """Generate the formatted header banner for this theme."""
        pass

    @abstractmethod
    def get_theme_color(self, name: str) -> str:
        """Retrieve color hex/code for a named theme token."""
        pass

    @abstractmethod
    def build_style(self, **overrides: str) -> Any:
        """Compile a complete style dictionary or Style object."""
        pass


BaseThemeEngine = BaseThemeRenderer


class BasePreferenceManager(ABC):
    """Abstract base class for user configuration and preferences storage."""

    @abstractmethod
    def load_preferences(self) -> Dict[str, Any]:
        """Load preferences dictionary from persistence."""
        pass

    @abstractmethod
    def save_preferences(self, prefs: Dict[str, Any]) -> None:
        """Persist preferences dictionary to storage."""
        pass


class BaseHistoryLedger(ABC):
    """Abstract base class for persistent session and activity logging."""

    @abstractmethod
    def record_event(self, entry: Dict[str, Any]) -> None:
        """Record an event into the history ledger."""
        pass

    @abstractmethod
    def load_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve historical events from the ledger."""
        pass


class BaseExportHandler(ABC):
    """Abstract base class for exporting code snippets and mission reports."""

    @abstractmethod
    def export(self, title: str, content: str, export_code: bool = True) -> Any:
        """Export content and optionally extract embedded code blocks."""
        pass


BaseExportManager = BaseExportHandler


class BaseInputHandler(ABC):
    """Abstract base class for interactive user prompts, dialogs, and confirmations."""

    @abstractmethod
    def ask_input(
        self,
        message: str,
        choices: Optional[List[str]] = None,
        default: str = "",
        password: bool = False,
    ) -> str:
        """Prompt user for text input."""
        pass

    @abstractmethod
    async def ask_choice(
        self,
        title: str,
        options: Dict[str, str],
        style_name: str = "plum1",
    ) -> str:
        """Prompt user to select from an interactive choice menu."""
        pass

    @abstractmethod
    def confirm(self, message: str, default: bool = True) -> bool:
        """Prompt user for a yes/no confirmation."""
        pass


BaseDialogHandler = BaseInputHandler
BaseInputReader = BaseInputHandler


class BaseSwarmFusionHandler(ABC):
    """Abstract contract for swarm multimodal fusion and prompt consensus."""

    @abstractmethod
    async def fuse_responses(self, responses: List[Dict[str, Any]], query: str) -> str:
        """Synthesize multiple model responses into a coherent consensus output."""
        pass


class BaseSwarmInspectorHandler(ABC):
    """Abstract contract for swarm state inspection and sandbox execution."""

    @abstractmethod
    def inspect_phase(self, phase_name: str, data: Dict[str, Any]) -> None:
        """Display telemetry and diagnostics for an active swarm phase."""
        pass


class BaseSwarmMissionHandler(ABC):
    """Abstract contract for running continuous or background swarm missions."""

    @abstractmethod
    async def execute_mission(self, mission_name: str, query: str) -> Any:
        """Run the continuous mission loop."""
        pass


BaseMenuHandler = BaseMenu
BaseEventManager = BaseHistoryLedger
IEventManager = IHistoryLedger
IInterfaceView = BaseInterfaceView
IMenu = BaseMenu
ITUIComponent = BaseTUIComponent
IThemeEngine = IThemingProvider
IDialogHandler = BaseDialogHandler
IInputReader = BaseInputReader
BaseTelemetryProvider = BaseTelemetryCollector
BaseThemeEngine = BaseThemeRenderer
BaseExportManager = BaseExportHandler


__all__ = [
    "BasePreferenceManager",
    "IPreferenceManager",
    "BaseInterfaceView",
    "IInterfaceView",
    "BaseMenu",
    "IMenu",
    "BaseMenuHandler",
    "IMenuHandler",
    "BaseTUIComponent",
    "ITUIComponent",
    "BaseTUIAppInterface",
    "ITUIApp",
    # ABCs
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
    "BaseInputReader",
    "BaseThemeEngine",
    "BaseTelemetryProvider",
    "BaseExportManager",
]
