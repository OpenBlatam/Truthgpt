"""
Unified Component Factory for TruthGPT Interface Subsystem.
===========================================================
Provides high-level factory instantiation functions for:
  - TUI Applications (create_tui_app)
  - Menu Controllers & Handlers (create_menu)
  - Theme Palettes & Style Engines (create_theme_engine)
  - Telemetry Providers (create_telemetry_provider)
  - Custom Interface Views (create_interface)
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from interface.builder import InterfaceBuilder, TUIAppBuilder, create_interface_builder, create_tui_builder
from interface.exceptions import MenuNotFoundError, ThemeNotFoundError
from interface.interfaces import BaseMenu, BaseThemeEngine
from interface.registry import MenuRegistry, ThemeRegistry
from interface.telemetry import TelemetryProvider
from interface.types import InterfaceMode, MenuItem, ThemePalette, ThemeType, TUIConfiguration


def create_interface(
    interface_type: str = "dashboard",
    theme: str = "claude",
    mode: Union[InterfaceMode, str] = InterfaceMode.EXTENDED,
    **kwargs: Any,
) -> Any:
    """Instantiate a configured interface or TUI application.

    Args:
        interface_type: 'dashboard', 'swarm', 'cli', 'headless'
        theme: 'claude', 'industrial', 'matrix', 'neon', 'minimalist'
        mode: InterfaceMode enum or string ('standard', 'extended', 'headless')
        **kwargs: Extra parameters passed to builder.
    """
    app_type = interface_type.lower().strip()
    if app_type in ("dashboard", "swarm", "interactive_dashboard", "interactive_swarm", "swarm_menu"):
        builder = create_tui_builder(app_type=app_type)
        builder.with_theme(theme)
        builder.with_mode(mode)
        if "active_agents" in kwargs:
            builder.with_active_agents(kwargs["active_agents"])
        if "extended" in kwargs:
            builder.with_extended(bool(kwargs["extended"]))
        return builder.build()

    # CLI / Custom View Builder
    builder = create_interface_builder(title=kwargs.get("title", "TruthGPT Interface"))
    builder.with_theme(theme)
    builder.with_mode(mode)
    return builder


def create_tui_app(
    app_type: str = "dashboard",
    extended: bool = True,
    theme: str = "claude",
    active_agents: Optional[List[Any]] = None,
    **kwargs: Any,
) -> Any:
    """Create a prompt_toolkit TUI application instance."""
    builder = create_tui_builder(app_type=app_type)
    builder.with_theme(theme)
    builder.with_extended(extended)
    if active_agents is not None:
        builder.with_active_agents(active_agents)
    return builder.build()


def create_menu(
    menu_name: str,
    **kwargs: Any,
) -> Union[MenuItem, BaseMenu, Callable[..., Any]]:
    """Retrieve or instantiate a registered menu.

    Args:
        menu_name: Registered menu ID (e.g. 'swarm', 'blockchain', 'model', 'history')
    """
    # 1. Check if class registered
    instance = MenuRegistry.create_menu_instance(menu_name, **kwargs)
    if instance:
        return instance

    # 2. Return MenuItem
    return MenuRegistry.get_menu(menu_name)


def create_theme_engine(
    theme_name: str = "claude",
) -> ThemePalette:
    """Retrieve the ThemePalette and styling tokens for a given theme name."""
    return ThemeRegistry.get_palette(theme_name)


def create_telemetry_provider() -> type[TelemetryProvider]:
    """Retrieve the TelemetryProvider class singleton."""
    return TelemetryProvider
