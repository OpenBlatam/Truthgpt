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

    # Minimum dimensions below which we switch to ultra-compact rendering
    MIN_COMPACT_HEIGHT: int = 20
    MIN_COMPACT_WIDTH: int = 60
    MIN_NARROW_WIDTH: int = 40

    def __init__(self) -> None:
        self.result: Optional[str] = None
        self.kb: KeyBindings = KeyBindings()
        self._console: Optional[Console] = None
        self.selected_index: int = 0
        self._setup_base_keybindings()

    # ── Terminal Dimension Helpers ─────────────────────────────────

    @staticmethod
    def get_terminal_dims() -> tuple:
        """Return (width, height) of the current terminal, with safe fallbacks."""
        size = shutil.get_terminal_size(fallback=(80, 24))
        w = max(20, size.columns or 80)
        h = max(5, size.lines or 24)
        return (w, h)

    @classmethod
    def is_compact_mode(cls) -> bool:
        """True when the terminal is too short for full-size UI elements."""
        w, h = cls.get_terminal_dims()
        return h < cls.MIN_COMPACT_HEIGHT or w < cls.MIN_COMPACT_WIDTH

    @classmethod
    def is_narrow(cls) -> bool:
        """True when terminal width is very constrained."""
        w, _ = cls.get_terminal_dims()
        return w < cls.MIN_NARROW_WIDTH

    # ── Rich Console ──────────────────────────────────────────────

    @property
    def console(self) -> Console:
        """Lazily create a Rich Console sized to the current terminal."""
        width = self.get_terminal_dims()[0]
        if self._console is None or self._console.width != width:
            self._console = Console(
                file=io.StringIO(), force_terminal=True, width=width
            )
        return self._console

    def reset_console(self) -> Console:
        """Reset the internal StringIO buffer and return the fresh console."""
        width = self.get_terminal_dims()[0]
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
        """Build and run the prompt_toolkit Application. Subclasses must implement `get_layout()`.

        Adapts to terminal size: uses a longer refresh interval on compact
        terminals and wraps the execution in a try/except so that rendering
        errors on very small windows fall back gracefully.
        """
        compact = self.is_compact_mode()
        refresh = 1.0 if compact else 0.5

        try:
            app = Application(
                layout=self.get_layout(),
                key_bindings=self.kb,
                style=self.build_style(),
                mouse_support=True,
                full_screen=True,
                refresh_interval=refresh,
                min_redraw_interval=0.3 if compact else 0.1,
            )
            await app.run_async()
        except Exception:
            # Fallback: if full_screen fails (e.g. extremely tiny terminal),
            # try to collect input via a simple Rich prompt instead.
            from rich.prompt import Prompt
            self.result = Prompt.ask("[bold cyan]Command[/bold cyan]")
        return self.result

    def get_layout(self) -> Any:
        """Subclasses must override this to return a prompt_toolkit Layout."""
        raise NotImplementedError("Subclasses must implement get_layout()")
