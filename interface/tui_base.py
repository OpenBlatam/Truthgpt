"""
BaseTUIApp — Shared Base Class for prompt_toolkit TUI Applications.
===================================================================
Eliminates duplicated keybinding, styling, mouse handling, and Rich->ANSI
rendering logic across all interactive interface menus and dashboards.
"""
from __future__ import annotations

import io
import shutil
from typing import Any, Callable, Dict, Optional

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console

from interface.config import USER_PREFS
from interface.constants import THEME_FOCUSED_COLORS
from interface.interfaces import BaseTUIAppInterface


class BaseTUIApp(BaseTUIAppInterface):
    """Base class for interactive TUI screens using prompt_toolkit + Rich."""

    def __init__(self) -> None:
        self.result: Optional[str] = None
        self.kb: KeyBindings = KeyBindings()
        self._console: Optional[Console] = None
        self.selected_index: int = 0
        self._setup_base_keybindings()

    # ── Rich Console ──────────────────────────────────────────────

    @property
    def console(self) -> Console:
        """Lazily create a Rich Console sized to the current terminal."""
        width = shutil.get_terminal_size().columns or 100
        if self._console is None or self._console.width != width:
            self._console = Console(
                file=io.StringIO(), force_terminal=True, width=width
            )
        return self._console

    def reset_console(self) -> Console:
        """Reset the internal StringIO buffer and return the fresh console."""
        width = shutil.get_terminal_size().columns or 100
        self._console = Console(
            file=io.StringIO(), force_terminal=True, width=width
        )
        return self._console

    def render_rich_to_ansi(self) -> ANSI:
        """Convert whatever was printed to self.console into ANSI formatted text."""
        return ANSI(self.console.file.getvalue())

    # ── Keybindings ───────────────────────────────────────────────

    def _setup_base_keybindings(self) -> None:
        """Register Ctrl+C and Escape as universal exit keys."""

        @self.kb.add("c-c")
        def _ctrl_c(event: Any) -> None:
            self.result = "exit"
            event.app.exit()

        @self.kb.add("escape")
        def _escape(event: Any) -> None:
            self.result = "exit"
            event.app.exit()

    def register_hotkey(self, key: str, val: str) -> None:
        """Bind a case-insensitive keyboard shortcut to trigger a specific choice value."""
        @self.kb.add(key.lower())
        @self.kb.add(key.upper())
        def _(event: Any, v: str = val) -> None:
            self.set_choice(v)

    def register_hotkeys(self, key_map: Any) -> None:
        """Bind a mapping or list of key shortcuts to choice return values."""
        if isinstance(key_map, dict):
            for k, v in key_map.items():
                self.register_hotkey(k, v)
        elif hasattr(key_map, "__iter__"):
            for k in key_map:
                self.register_hotkey(str(k), str(k))

    def set_choice(self, val: str) -> None:
        """Convenience: set self.result and exit the running application."""
        self.result = val
        try:
            get_app().exit(result=val)
        except Exception:
            pass

    # ── Theming ───────────────────────────────────────────────────

    @staticmethod
    def current_theme() -> str:
        """Get the active user theme preference."""
        return USER_PREFS.get("theme", "industrial")

    @staticmethod
    def is_claude_theme() -> bool:
        """Check if active theme belongs to Claude/Minimalist family."""
        return USER_PREFS.get("theme", "industrial") in (
            "claude", "anthropic", "minimalist",
        )

    def build_style(self, **overrides: Any) -> Style:
        """Return a theme-aware Style dict, merged with optional overrides."""
        theme = self.current_theme()
        is_claude = self.is_claude_theme()
        focused_color = THEME_FOCUSED_COLORS.get(theme, "#ffbbff")

        base = {
            "dot": "bold cyan",
            "id": "bold white",
            "name": "white",
            "cursorline": "underline cyan",
            "button": "white" if is_claude else "bold white bg:black",
            "button.focused": (
                "bold cyan underline"
                if is_claude
                else f"bold white bg:{focused_color}"
            ),
            "label": "bold cyan",
            "frame.label": "bold #ffbbff",
            # Footer
            "prompt_seg": "bg:cyan black bold",
            "shortcut_seg": "bg:white black bold",
            "shortcut_label": "white",
            "load_label": "dim",
            "load_bar": "bold green",
            "session_seg": "bg:#333333 white bold",
            "version_seg": "bg:#222222 dim",
            # Command input
            "command_input": "bold cyan",
            "command_input.prompt": "bold cyan",
        }
        base.update(overrides)
        return Style.from_dict(base)

    # ── Application Runner ────────────────────────────────────────

    async def run(self) -> Optional[str]:
        """Build and run the prompt_toolkit Application. Subclasses must implement `get_layout()`."""
        app = Application(
            layout=self.get_layout(),
            key_bindings=self.kb,
            style=self.build_style(),
            mouse_support=True,
            full_screen=True,
            refresh_interval=0.5,
        )
        await app.run_async()
        return self.result

    def get_layout(self) -> Any:
        """Subclasses must override this to return a prompt_toolkit Layout."""
        raise NotImplementedError("Subclasses must implement get_layout()")
