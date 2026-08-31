"""
Declarative Interface & TUI Application Builders for TruthGPT.
==============================================================
Provides fluent builders for assembling:
  - TUI Application instances (TUIAppBuilder)
  - Custom Interface Views and CLI Dashboards (InterfaceBuilder)
  - Layout Grids (DashboardLayoutBuilder, MenuLayoutBuilder)
  - Header Panels (HeaderBuilder)
  - Menu Descriptors (MenuBuilder, DashboardBuilder)
"""
from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.builder":
        sys.modules["interface.builder"] = _mod
    elif __name__ == "interface.builder":
        sys.modules["optimization_core.interface.builder"] = _mod

from interface.exceptions import LayoutRenderError
from interface.interfaces import BaseMenu, BaseTUIComponent
from interface.types import (
    InterfaceMode,
    MenuItem,
    MenuOption,
    ThemePalette,
    ThemeType,
    TUIConfiguration,
)


class MenuBuilder:
    """Fluent builder for composing dynamic interactive menus and item collections."""

    def __init__(self, title: str = "Custom Menu") -> None:
        self.title = title
        self._items: List[MenuItem] = []
        self._category: str = "general"

    def set_category(self, category: str) -> MenuBuilder:
        self._category = category
        return self

    def with_category(self, category: str) -> MenuBuilder:
        self._category = category
        return self

    def add_option(
        self,
        key: str,
        title: str,
        handler: Optional[Callable[..., Any]] = None,
        description: str = "",
        shortcut: Optional[str] = None,
        icon: str = "📌",
    ) -> MenuBuilder:
        item = MenuItem(
            id=key,
            key=key,
            title=title,
            name=title,
            handler=handler,
            category=self._category,
            description=description,
            shortcut=shortcut or key,
            icon=icon,
        )
        self._items.append(item)
        return self

    def add_item(
        self,
        key: str,
        name: str,
        handler: Optional[Callable[..., Any]] = None,
        description: str = "",
        icon: str = "🔹",
        shortcut: Optional[str] = None,
    ) -> MenuBuilder:
        item = MenuItem(
            id=key,
            name=name,
            key=key,
            title=name,
            handler=handler,
            category=self._category,
            description=description,
            shortcut=shortcut or key,
            icon=icon,
        )
        self._items.append(item)
        return self

    @property
    def options(self) -> List[MenuItem]:
        return self._items

    @property
    def category(self) -> str:
        return self._category

    def build(self) -> Dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "category": self._category,
            "options": self._items,
        }


class HeaderBuilder:
    """Fluent builder for creating Rich header panels and HUD banners."""

    def __init__(self, text: str = "TruthGPT OS") -> None:
        self.text = text
        self.style = "plum1"
        self.subtitle = ""
        self.border_style = "plum1"
        self._updates: Optional[List[str]] = None

    def with_theme(self, theme: str) -> HeaderBuilder:
        self.style = "cyan" if theme in ("claude", "anthropic") else "magenta"
        self.border_style = self.style
        return self

    def with_updates(self, updates: List[str]) -> HeaderBuilder:
        self._updates = updates
        return self

    def set_style(self, style: str) -> HeaderBuilder:
        self.style = style
        return self

    def set_subtitle(self, subtitle: str) -> HeaderBuilder:
        self.subtitle = subtitle
        return self

    def set_border(self, border: str) -> HeaderBuilder:
        self.border_style = border
        return self

    def build(self) -> Any:
        try:
            from interface.theming import get_claude_header, get_header
            if self.style in ("cyan", "plum1"):
                return get_claude_header(updates=self._updates)
            return get_header()
        except Exception:
            from rich.panel import Panel
            from rich.text import Text
            content = Text(self.text, style=f"bold {self.style}", justify="center")
            return Panel(
                content,
                title=f"[bold {self.style}] {self.text} [/bold {self.style}]",
                subtitle=f"[dim] {self.subtitle} [/dim]" if self.subtitle else None,
                border_style=self.border_style,
                padding=(1, 2),
            )


class DashboardLayoutBuilder:
    """Builder for assembling TUI dashboard split layout grids and views."""

    def __init__(self) -> None:
        self._components: List[Any] = []
        self._extended: bool = True
        self._theme: str = "claude"

    def add_component(self, comp: Any) -> DashboardLayoutBuilder:
        self._components.append(comp)
        return self

    def with_extended(self, extended: bool) -> DashboardLayoutBuilder:
        self._extended = extended
        return self

    def with_theme(self, theme: str) -> DashboardLayoutBuilder:
        self._theme = theme
        return self

    def build_layout(self) -> Any:
        try:
            from prompt_toolkit.layout.containers import HSplit
            return HSplit(self._components)
        except Exception:
            return self._components

    def build(self) -> Any:
        from interface.interactive_dashboard import InteractiveDashboardApp
        return InteractiveDashboardApp(extended=self._extended)


class MenuLayoutBuilder:
    """Builder for assembling vertical or horizontal menu item layouts."""

    def __init__(self) -> None:
        self._items: List[Any] = []
        self._padding: int = 1

    def add_item(self, item: Any) -> MenuLayoutBuilder:
        self._items.append(item)
        return self

    def set_padding(self, padding: int) -> MenuLayoutBuilder:
        self._padding = padding
        return self

    def build(self) -> Any:
        try:
            from prompt_toolkit.layout.containers import HSplit
            return HSplit(self._items, padding=self._padding)
        except Exception:
            return self._items


DashboardBuilder = DashboardLayoutBuilder


class TUIAppBuilder:
    """Fluent builder for prompt_toolkit TUI applications."""

    def __init__(self, app_type: str = "dashboard") -> None:
        self.app_type = app_type
        self._theme: str = "claude"
        self._extended: bool = True
        self._mouse_support: bool = True
        self._full_screen: bool = True
        self._refresh_interval: float = 0.5
        self._command_prompt: str = " ❯ "
        self._menu_items: List[MenuItem] = []
        self._custom_keybindings: Dict[str, Callable[..., Any]] = {}
        self._custom_styles: Dict[str, str] = {}
        self._active_agents: Optional[List[Any]] = None

    def with_theme(self, theme: Union[ThemeType, str]) -> TUIAppBuilder:
        """Set the active theme name."""
        self._theme = theme.value if isinstance(theme, ThemeType) else str(theme)
        return self

    def with_mode(self, mode: Union[InterfaceMode, str]) -> TUIAppBuilder:
        """Set standard or extended interface mode."""
        mode_val = mode.value if isinstance(mode, InterfaceMode) else str(mode)
        self._extended = (mode_val != "standard" and mode_val != "minimal")
        return self

    def with_extended(self, extended: bool) -> TUIAppBuilder:
        """Enable or disable extended header/status panels."""
        self._extended = extended
        return self

    def with_mouse_support(self, enabled: bool) -> TUIAppBuilder:
        """Enable or disable mouse click navigation."""
        self._mouse_support = enabled
        return self

    def with_full_screen(self, enabled: bool) -> TUIAppBuilder:
        """Enable or disable fullscreen alternative buffer."""
        self._full_screen = enabled
        return self

    def with_refresh_interval(self, interval: float) -> TUIAppBuilder:
        """Set application event loop polling interval."""
        self._refresh_interval = max(0.05, float(interval))
        return self

    def with_prompt(self, prompt: str) -> TUIAppBuilder:
        """Set input line prompt symbol."""
        self._command_prompt = prompt
        return self

    def with_command_prompt(self, prompt_text: str) -> TUIAppBuilder:
        """Set input line prompt symbol alias."""
        self._command_prompt = prompt_text
        return self

    def add_menu_item(
        self,
        shortcut: str,
        name: str,
        handler: Optional[Callable[..., Any]] = None,
        description: str = "",
        icon: str = "🔹",
    ) -> TUIAppBuilder:
        """Add a navigation menu action to the application."""
        self._menu_items.append(
            MenuItem(
                id=shortcut,
                name=name,
                key=shortcut,
                title=name,
                handler=handler,
                description=description,
                shortcut=shortcut,
                icon=icon,
            )
        )
        return self

    def add_keybinding(self, key_combination: str, handler: Callable[..., Any]) -> TUIAppBuilder:
        """Register custom key combination."""
        self._custom_keybindings[key_combination] = handler
        return self

    def add_style(self, token_name: str, style_spec: str) -> TUIAppBuilder:
        """Override prompt_toolkit CSS token."""
        self._custom_styles[token_name] = style_spec
        return self

    def with_style_override(self, token: str, style_def: str) -> TUIAppBuilder:
        """Override prompt_toolkit CSS token alias."""
        self._custom_styles[token] = style_def
        return self

    def with_active_agents(self, agents: List[Any]) -> TUIAppBuilder:
        """Inject active agents list."""
        self._active_agents = agents
        return self

    def build_config(self) -> TUIConfiguration:
        """Assemble and return structured TUIConfiguration."""
        return TUIConfiguration(
            refresh_interval=self._refresh_interval,
            mouse_support=self._mouse_support,
            full_screen=self._full_screen,
            theme=self._theme,
            extended_mode=self._extended,
            custom_styles=self._custom_styles,
        )

    def build(self) -> Any:
        """Construct the concrete BaseTUIApp instance."""
        if self.app_type == "dashboard":
            from interface.interactive_dashboard import InteractiveDashboardApp
            app = InteractiveDashboardApp(extended=self._extended)
        elif self.app_type == "swarm":
            from interface.interactive_swarm import InteractiveSwarmApp
            app = InteractiveSwarmApp(active_agents=self._active_agents)
        elif self.app_type == "models":
            from interface.model_menu import ModelMenuApp
            app = ModelMenuApp()
        else:
            from interface.interactive_dashboard import InteractiveDashboardApp
            app = InteractiveDashboardApp(extended=self._extended)

        for key, fn in self._custom_keybindings.items():
            try:
                app.kb.add(key)(fn)
            except Exception:
                pass

        return app


class InterfaceBuilder:
    """Declarative builder for custom terminal views, dashboards, and menus."""

    def __init__(self, title: str = "TruthGPT Interface") -> None:
        self.title = title
        self._theme: str = "claude"
        self._mode: InterfaceMode = InterfaceMode.EXTENDED
        self._show_header: bool = True
        self._show_telemetry: bool = True
        self._show_balances: bool = True
        self._menus: List[MenuItem] = []
        self._custom_panels: List[Tuple[str, str]] = []

    def with_theme(self, theme: Union[ThemeType, str]) -> InterfaceBuilder:
        self._theme = theme.value if isinstance(theme, ThemeType) else str(theme)
        return self

    def with_mode(self, mode: Union[InterfaceMode, str]) -> InterfaceBuilder:
        self._mode = mode if isinstance(mode, InterfaceMode) else InterfaceMode(str(mode).lower())
        return self

    def with_header(self, enabled: bool = True) -> InterfaceBuilder:
        self._show_header = enabled
        return self

    def with_telemetry(self, enabled: bool = True) -> InterfaceBuilder:
        self._show_telemetry = enabled
        return self

    def with_balances(self, enabled: bool = True) -> InterfaceBuilder:
        self._show_balances = enabled
        return self

    def add_menu(self, menu_item: MenuItem) -> InterfaceBuilder:
        self._menus.append(menu_item)
        return self

    def add_custom_panel(self, title: str, content: str) -> InterfaceBuilder:
        self._custom_panels.append((title, content))
        return self

    def create_tui_builder(self) -> TUIAppBuilder:
        """Create a linked TUIAppBuilder with inherited settings."""
        builder = TUIAppBuilder()
        builder.with_theme(self._theme)
        builder.with_mode(self._mode)
        for m in self._menus:
            if m.shortcut:
                builder.add_menu_item(m.shortcut, m.name, m.handler, m.description, m.icon)
        return builder

    def build(self) -> Any:
        return self.create_tui_builder().build()


# ---------------------------------------------------------------------------
# Factory Helper Functions
# ---------------------------------------------------------------------------

def create_interface(title: str = "TruthGPT Interface") -> InterfaceBuilder:
    """Factory helper to start building a custom Interface."""
    return InterfaceBuilder(title=title)


def create_menu(title: str = "Custom Menu") -> MenuBuilder:
    """Factory helper to create a MenuBuilder."""
    return MenuBuilder(title=title)


def create_telemetry_provider() -> Any:
    """Factory helper for TelemetryProvider."""
    from interface.telemetry import TelemetryProvider
    return TelemetryProvider


def create_theme_engine(name: str = "claude") -> Any:
    """Factory helper for ThemeRegistry / ThemePalette."""
    from interface.registry import ThemeRegistry
    return ThemeRegistry.get_theme(name)


def create_tui_app(app_type: str = "dashboard") -> Any:
    """Factory helper to start building a TUI application."""
    builder = TUIAppBuilder(app_type=app_type)
    return builder.build()


def create_interface_builder(title: str = "TruthGPT Interface") -> InterfaceBuilder:
    """Factory helper to start building a custom Interface."""
    return InterfaceBuilder(title=title)


def create_tui_builder(app_type: str = "dashboard") -> TUIAppBuilder:
    """Factory helper to start building a TUI application."""
    return TUIAppBuilder(app_type=app_type)


__all__ = [
    "MenuBuilder",
    "HeaderBuilder",
    "DashboardLayoutBuilder",
    "DashboardBuilder",
    "MenuLayoutBuilder",
    "TUIAppBuilder",
    "InterfaceBuilder",
    "create_interface",
    "create_menu",
    "create_telemetry_provider",
    "create_theme_engine",
    "create_tui_app",
    "create_interface_builder",
    "create_tui_builder",
]
