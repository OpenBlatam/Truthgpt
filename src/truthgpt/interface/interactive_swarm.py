"""
Interactive Swarm — Button-grid TUI for the Swarm Intelligence Hub.

Refactored to use BaseTUIApp for shared keybinding/styling logic.
Fixed: ANSI import was missing (runtime bug).
"""

import io

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.containers import VSplit, HSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Button, Box, Shadow, Label

from truthgpt.interface.core import (
    console as rich_console, USER_PREFS, get_header,
)
from truthgpt.interface.tui_base import BaseTUIApp


class InteractiveSwarmApp(BaseTUIApp):
    def __init__(self, active_agents):
        super().__init__()
        self.active_agents = active_agents

        # Add hotkeys for each option
        for char in "ACPVBSXFTME0":
            @self.kb.add(char.lower())
            @self.kb.add(char.upper())
            def _(event, c=char):
                self.result = c
                event.app.exit()

        # Also allow 'q' to quit
        @self.kb.add('q')
        def _(event):
            self.result = "0"
            event.app.exit()

    def render_rich_content(self):
        c = self.reset_console()
        c.print(get_header())

        if self.is_claude_theme():
            from truthgpt.interface.cc_style import cc_action
            c.print()
            cc_action("Swarm Intelligence Hub - Specialized Experts Ready", status="INFO")
            c.print()
        else:
            c.print(Panel(
                f" [bold magenta]Swarm Intelligence Hub - Industrial Command Center[/bold magenta]\n"
                f" [dim]{len(self.active_agents)} Specialized Experts Ready for Deployment[/dim]",
                border_style="magenta",
            ))

        table = Table(box=None, padding=(0, 2))
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Expert", style="bold white")
        table.add_column("Specialization", style="green")
        table.add_column("Status", style="dim")

        for i, agent in enumerate(self.active_agents, 1):
            role = getattr(agent, "role", "Strategic Expert")
            table.add_row(str(i), agent.name.upper(), role, "[green]● Online[/green]")

        c.print(table)
        c.print("[dim]────────────────────────────────────────────────────────────────────────────────[/dim]")

        return self.render_rich_to_ansi()

    def get_layout(self):
        def make_btn(text, val):
            return Button(text, handler=lambda: self.set_choice(val), width=35)

        row1 = VSplit([make_btn("A: Ask Swarm (Auto-Routing)", "A"), make_btn("F: Dynamic Swarm Fusion", "F")], padding=4, align=WindowAlign.CENTER)
        row2 = VSplit([make_btn("C: Continuous Mission (Auto)", "C"), make_btn("B: Background Missions (📡)", "B")], padding=4, align=WindowAlign.CENTER)
        row3 = VSplit([make_btn("P: Persona Tuning (Deep AI)", "P"), make_btn("E: Expert Matrix (Tool View)", "E")], padding=4, align=WindowAlign.CENTER)
        row4 = VSplit([make_btn("V: Neural Vault (Memory)", "V"), make_btn("M: MCP Connectors", "M")], padding=4, align=WindowAlign.CENTER)
        row5 = VSplit([make_btn("S: Swarm Status (Telemetría)", "S"), make_btn("T: Math & Verification", "T")], padding=4, align=WindowAlign.CENTER)
        row6 = VSplit([make_btn("X: Agent Composer (Build)", "X"), make_btn("0: Back to Kernel Dashboard", "0")], padding=4, align=WindowAlign.CENTER)

        static_content = FormattedTextControl(text=self.render_rich_content)

        footer_label = (
            " [bold white]❯[/bold white] [dim]Select Option[/dim]"
            if self.is_claude_theme()
            else " [bold cyan]🖱️ Mouse Active[/bold cyan]"
        )

        root_container = HSplit([
            Window(content=static_content, wrap_lines=True, ignore_content_height=True),
            HSplit([row1, row2, row3, row4, row5, row6], padding=1),
            Window(height=1, char=" "),
            Box(Label(f"{footer_label} [dim]• Click any option or use Hotkeys (A, C, P...)[/dim]", style="italic"), padding=1),
        ], align=WindowAlign.CENTER)

        if self.is_claude_theme():
            return Layout(root_container)
        return Layout(Shadow(Box(root_container, padding=1)))

    def build_style(self, **overrides):
        """Swarm-specific style overrides."""
        focused_color = "cyan" if self.is_claude_theme() else "magenta"
        return super().build_style(
            **{
                "button.focused": (
                    "bold cyan underline"
                    if self.is_claude_theme()
                    else f"bold white bg:{focused_color}"
                ),
                "button.text": "white",
                "frame.label": "bold magenta",
                "shadow": "bg:gray",
                **overrides,
            }
        )


async def get_interactive_choice(active_agents):
    app = InteractiveSwarmApp(active_agents)
    return await app.run()
