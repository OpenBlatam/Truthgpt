"""
Theme Management & Visual Rendering Engine for TruthGPT Interface.
===================================================================
Provides theme palette configurations, ASCII banners, Claude Code style headers,
themed panels, and futuristic boot sequences.
"""
from __future__ import annotations

from typing import Any, List, Optional
from rich.panel import Panel
from rich.text import Text

from interface.interfaces import BaseThemeRenderer
from interface.theming import (
    get_claude_header,
    get_header,
    get_theme_color,
    get_theme_panel,
    linux_boot_sequence,
)
from interface.types import ThemeConfig, ThemeType


class ThemeRenderer(BaseThemeRenderer):
    """Concrete implementation of BaseThemeRenderer contract."""

    def get_header(self) -> Panel:
        return get_header()

    def get_theme_color(self) -> str:
        return get_theme_color()

    def get_theme_panel(
        self,
        content: Any,
        title: Optional[str] = None,
        border_style: Optional[str] = None,
    ) -> Panel:
        return get_theme_panel(content, title=title, border_style=border_style)


__all__ = [
    "ThemeRenderer",
    "get_header",
    "get_claude_header",
    "get_theme_color",
    "get_theme_panel",
    "linux_boot_sequence",
]
