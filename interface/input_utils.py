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
    """Displays a full-screen interactive choice menu with mouse and hotkey support."""
    if not _check_prompt_toolkit():
        from rich.prompt import Prompt
        from rich.table import Table

        table = Table(title=title)
        for k, v in options.items():
            table.add_row(k, v)
        console.print(table)
        return Prompt.ask("Select", choices=list(options.keys()))

    from prompt_toolkit.application import Application, get_app
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import Box, Button, Label, Shadow
    from rich.console import Console as RichConsole

    class SimpleMenuApp:
        def __init__(self):
            self.result: Optional[str] = None
            self.kb = KeyBindings()

            @self.kb.add("q")
            @self.kb.add("c-c")
            def _(event):
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

            buttons = []
            for k, v in options.items():
                label = f" < {k:>8}: {v:<25} > "
                buttons.append(
                    Button(
                        label,
                        handler=lambda val=k: set_choice(val),
                        width=50,
                    )
                )

            header_console = RichConsole(
                file=io.StringIO(), force_terminal=True, width=100
            )
            header_console.print(get_header())
            header_content = ANSI(header_console.file.getvalue())

            root = HSplit(
                [
                    Window(
                        content=FormattedTextControl(header_content),
                        ignore_content_height=True,
                    ),
                    Window(height=1),
                    Label(
                        f"  [bold {style_name}] {title.upper()} [/bold {style_name}]",
                        style="bold white",
                    ),
                    Window(height=1),
                    HSplit(buttons, padding=1),
                    Window(height=1),
                    Label(
                        "   [dim]Click or press key to select[/dim]",
                        style="italic",
                    ),
                    Window(height=1),
                ],
                align=WindowAlign.CENTER,
            )

            return Layout(Shadow(Box(root, padding=2)))

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

            app = Application(
                layout=self.get_layout(),
                key_bindings=self.kb,
                style=Style.from_dict({"button.focused": f"bg:{pt_style} white"}),
                mouse_support=True,
                full_screen=True,
            )
            await app.run_async()
            return self.result

    app = SimpleMenuApp()
    return await app.run()
