"""
Interactive User Input & Choice Handlers for TruthGPT Interface.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from interface.console import console
from interface.theming import get_header

_HAS_PROMPT_TOOLKIT: Optional[bool] = None


def _check_prompt_toolkit() -> bool:
    """Check if prompt_toolkit is available in the Python runtime."""
    global _HAS_PROMPT_TOOLKIT
    if _HAS_PROMPT_TOOLKIT is None:
        try:
            import prompt_toolkit

            _HAS_PROMPT_TOOLKIT = True
        except ImportError:
            _HAS_PROMPT_TOOLKIT = False
    return _HAS_PROMPT_TOOLKIT


def _build_ctrl_o_keybindings() -> Optional[Any]:
    """Build a prompt_toolkit KeyBindings object with ctrl+o => expand pending blocks."""
    try:
        from prompt_toolkit.key_binding import KeyBindings
    except Exception:
        return None
    kb = KeyBindings()

    @kb.add("c-o")
    def _expand(event):
        try:
            from interface.cc_style import expand_pending

            event.app.run_in_terminal(lambda: expand_pending())
        except Exception:
            pass

    return kb


def get_input(
    message: str,
    choices: Optional[List[str]] = None,
    default: str = "",
    password: bool = False,
) -> str:
    """Gets user input with mouse support if available, otherwise fallbacks to Rich."""
    if _check_prompt_toolkit():
        try:
            import asyncio

            asyncio.get_running_loop()
            in_loop = True
        except RuntimeError:
            in_loop = False

        if not in_loop:
            try:
                from prompt_toolkit import prompt as pt_prompt
                from prompt_toolkit.styles import Style as PTStyle

                style = PTStyle.from_dict({"prompt": "bold cyan"})
                kb = _build_ctrl_o_keybindings()
                result = pt_prompt(
                    f"{message}: ",
                    mouse_support=True,
                    style=style,
                    is_password=password,
                    key_bindings=kb,
                ).strip()
                if not result and default:
                    return default
                return result
            except (EOFError, KeyboardInterrupt):
                return "0"
            except Exception:
                pass

    from rich.prompt import Prompt

    return Prompt.ask(message, choices=choices, default=default, password=password)


async def get_choice(
    title: str,
    options: Dict[str, str],
    style_name: str = "plum1",
) -> str:
    """Displays a full-screen interactive choice menu with mouse and hotkey support.

    Adapts dynamically to terminal size: uses compact layouts for small
    terminals and falls back to a plain Rich prompt on extremely tiny windows.
    """
    if not _check_prompt_toolkit():
        from rich.prompt import Prompt
        from rich.table import Table

        table = Table(title=title)
        for k, v in options.items():
            table.add_row(k, v)
        console.print(table)
        return Prompt.ask("Select", choices=list(options.keys()))

    import shutil

    from prompt_toolkit.application import Application, get_app
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign, ScrollablePane
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import Box, Button, Label, Shadow
    from rich.console import Console as RichConsole

    # Get current terminal dimensions
    term_size = shutil.get_terminal_size(fallback=(80, 24))
    term_w = max(20, term_size.columns or 80)
    term_h = max(5, term_size.lines or 24)
    compact = term_h < 20 or term_w < 60
    ultra_compact = term_h < 10 or term_w < 40

    # On extremely tiny terminals, fall back to simple prompt
    if ultra_compact:
        from rich.prompt import Prompt
        from rich.table import Table

        table = Table(title=title, width=min(term_w - 2, 60))
        for k, v in options.items():
            table.add_row(k, v)
        console.print(table)
        return Prompt.ask("Select", choices=list(options.keys()))

    class SimpleMenuApp:
        def __init__(self):
            self.result: Optional[str] = None
            self.kb = KeyBindings()

            @self.kb.add("q")
            @self.kb.add("c-c")
            def _(event):
                event.app.exit()

            @self.kb.add("escape")
            def _esc(event):
                event.app.exit()

            for k in options.keys():

                @self.kb.add(k.lower())
                @self.kb.add(k.upper())
                def _(event, val=k):
                    self.result = val
                    event.app.exit()

        def get_layout(self) -> Layout:
            def set_choice(val):
                self.result = val
                get_app().exit(result=val)

            # Dynamic button width based on terminal width
            btn_width = max(20, min(50, term_w - 10))

            buttons = []
            for k, v in options.items():
                # Truncate label if needed for narrow terminals
                max_label_len = btn_width - 10
                display_v = v[:max_label_len] if len(v) > max_label_len else v
                label = f" < {k:>8}: {display_v:<{max_label_len}} > "
                buttons.append(
                    Button(
                        label,
                        handler=lambda val=k: set_choice(val),
                        width=btn_width,
                    )
                )

            # Use actual terminal width for header console
            header_width = max(40, term_w - 4)
            header_console = RichConsole(
                file=io.StringIO(), force_terminal=True, width=header_width
            )
            header_console.print(get_header())
            header_content = ANSI(header_console.file.getvalue())

            # Truncate title to available width
            display_title = title[:term_w - 10] if len(title) > term_w - 10 else title

            content_parts = [
                Window(
                    content=FormattedTextControl(header_content),
                    ignore_content_height=True,
                    wrap_lines=True,
                ),
            ]

            if not compact:
                content_parts.append(Window(height=1))

            content_parts.extend([
                Label(
                    f"  [bold {style_name}] {display_title.upper()} [/bold {style_name}]",
                    style="bold white",
                ),
            ])

            if not compact:
                content_parts.append(Window(height=1))

            content_parts.extend([
                HSplit(buttons, padding=0 if compact else 1),
            ])

            if not compact:
                content_parts.extend([
                    Window(height=1),
                    Label(
                        "   [dim]Click or press key to select[/dim]",
                        style="italic",
                    ),
                    Window(height=1),
                ])

            if compact:
                # On compact terminals, wrap everything in a scrollable pane
                root = ScrollablePane(
                    HSplit(content_parts, align=WindowAlign.CENTER)
                )
            else:
                root = HSplit(content_parts, align=WindowAlign.CENTER)

            # Only add Shadow and Box padding on large terminals
            if not compact:
                return Layout(Shadow(Box(root, padding=2)))
            else:
                return Layout(root)

        async def run(self) -> Optional[str]:
            pt_style = style_name
            if pt_style == "plum1":
                pt_style = "#ffbbff"
            elif pt_style == "cyan":
                pt_style = "ansicyan"
            elif pt_style == "green":
                pt_style = "ansigreen"
            elif pt_style == "red":
                pt_style = "ansired"

            try:
                app = Application(
                    layout=self.get_layout(),
                    key_bindings=self.kb,
                    style=Style.from_dict({"button.focused": f"bg:{pt_style} white"}),
                    mouse_support=True,
                    full_screen=True,
                    min_redraw_interval=0.3 if compact else 0.1,
                )
                await app.run_async()
            except Exception:
                # Fallback on rendering failure
                from rich.prompt import Prompt
                self.result = Prompt.ask(
                    "[bold cyan]Select[/bold cyan]",
                    choices=list(options.keys()),
                )
            return self.result

    app = SimpleMenuApp()
    return await app.run()

