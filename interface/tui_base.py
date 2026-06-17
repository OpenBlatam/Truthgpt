"""
BaseTUIApp — Shared base class for prompt_toolkit TUI applications.
Eliminates duplicated keybinding, styling, and Rich→ANSI rendering logic
across interactive_dashboard.py and interactive_swarm.py.
"""

import io
import shutil
from typing import Optional

from rich.console import Console
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.styles import Style

from interface.core import USER_PREFS


class BaseTUIApp:
    """Base class for interactive TUI screens using prompt_toolkit + Rich."""

    def __init__(self):
        self.result: Optional[str] = None
        self.kb = KeyBindings()
        self._console: Optional[Console] = None
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
        """Reset the internal StringIO buffer and return the console."""
        width = shutil.get_terminal_size().columns or 100
        self._console = Console(
            file=io.StringIO(), force_terminal=True, width=width
        )
        return self._console

    def render_rich_to_ansi(self) -> ANSI:
        """Convert whatever was printed to self.console into ANSI formatted text."""
        return ANSI(self.console.file.getvalue())

    # ── Keybindings ───────────────────────────────────────────────

    def _setup_base_keybindings(self):
        """Register Ctrl+C and Escape as universal exit keys."""

        @self.kb.add("c-c")
        def _ctrl_c(event):
            self.result = "exit"
            event.app.exit()

        @self.kb.add("escape")
        def _escape(event):
            self.result = "exit"
            event.app.exit()

    def set_choice(self, val: str):
        """Convenience: set self.result and exit the running application."""
        from prompt_toolkit.application import get_app

        self.result = val
        get_app().exit(result=val)

    # ── Theming ───────────────────────────────────────────────────

    @staticmethod
    def current_theme() -> str:
        return USER_PREFS.get("theme", "industrial")

    @staticmethod
    def is_claude_theme() -> bool:
        return USER_PREFS.get("theme", "industrial") in (
            "claude", "anthropic", "minimalist",
        )

    def build_style(self, **overrides) -> Style:
        """Return a theme-aware Style dict, merged with optional overrides."""
        theme = self.current_theme()
        is_claude = self.is_claude_theme()
        focused_color = "#00ffff" if is_claude else "#ffbbff"

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
        """Build and run the prompt_toolkit Application. Subclasses must
        implement ``get_layout()``."""
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

    def get_layout(self):
        """Subclasses must override this to return a prompt_toolkit Layout."""
        raise NotImplementedError
