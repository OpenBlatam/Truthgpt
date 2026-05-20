
import asyncio
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import io


from interface.core import (
    console as rich_console, USER_PREFS, get_header
)

class InteractiveSwarmApp:
    def __init__(self, active_agents):
        self.active_agents = active_agents
        self.result = None
        from prompt_toolkit.key_binding import KeyBindings
        self.kb = KeyBindings()
        self._setup_keybindings()
        self.console = Console(file=io.StringIO(), force_terminal=True, width=100)
        
    def _setup_keybindings(self):
        @self.kb.add('q')
        @self.kb.add('c-c')
        def _(event):
            self.result = "0"
            event.app.exit()

        # Add hotkeys for each option
        for char in "ACPVBSXFTME0":
            @self.kb.add(char.lower())
            @self.kb.add(char.upper())
            def _(event, c=char):
                self.result = c
                event.app.exit()

    def render_rich_content(self):
        theme = USER_PREFS.get("theme", "industrial")
        # Clear the internal string buffer
        self.console.file = io.StringIO()
        
        # Render the header
        self.console.print(get_header())
        
        if theme in ["claude", "anthropic", "minimalist"]:
            from interface.cc_style import cc_action
            self.console.print()
            cc_action("Swarm Intelligence Hub - Specialized Experts Ready", status="INFO")
            self.console.print()
        else:
            # Render the agents table
            self.console.print(Panel(f" [bold magenta]Swarm Intelligence Hub - Industrial Command Center[/bold magenta]\n [dim]{len(self.active_agents)} Specialized Experts Ready for Deployment[/dim]", border_style="magenta"))
        
        table = Table(box=None, padding=(0, 2))
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Expert", style="bold white")
        table.add_column("Specialization", style="green")
        table.add_column("Status", style="dim")
        
        for i, agent in enumerate(self.active_agents, 1):
            role = getattr(agent, "role", "Strategic Expert")
            status = "[green]● Online[/green]"
            table.add_row(str(i), agent.name.upper(), role, status)
        
        self.console.print(table)
        self.console.print("[dim]────────────────────────────────────────────────────────────────────────────────[/dim]")
        
        return ANSI(self.console.file.getvalue())

    def get_layout(self):
        from prompt_toolkit.application import get_app
        from prompt_toolkit.layout.containers import VSplit, HSplit, Window, WindowAlign
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.widgets import Button, Box, Shadow, Label
        from prompt_toolkit.layout.layout import Layout
        
        def set_choice(val):
            self.result = val
            get_app().exit(result=val)

        def make_btn(text, val):
            return Button(text, handler=lambda: set_choice(val), width=35)

        # Create clickable buttons that look like the grid
        row1 = VSplit([
            make_btn("A: Ask Swarm (Auto-Routing)", "A"),
            make_btn("F: Dynamic Swarm Fusion", "F"),
        ], padding=4, align=WindowAlign.CENTER)
        
        row2 = VSplit([
            make_btn("C: Continuous Mission (Auto)", "C"),
            make_btn("B: Background Missions (📡)", "B"),
        ], padding=4, align=WindowAlign.CENTER)
        
        row3 = VSplit([
            make_btn("P: Persona Tuning (Deep AI)", "P"),
            make_btn("E: Expert Matrix (Tool View)", "E"),
        ], padding=4, align=WindowAlign.CENTER)
        
        row4 = VSplit([
            make_btn("V: Neural Vault (Memory)", "V"),
            make_btn("M: MCP Connectors", "M"),
        ], padding=4, align=WindowAlign.CENTER)
        
        row5 = VSplit([
            make_btn("S: Swarm Status (Telemetría)", "S"),
            make_btn("T: Math & Verification", "T"),
        ], padding=4, align=WindowAlign.CENTER)
        
        row6 = VSplit([
            make_btn("X: Agent Composer (Build)", "X"),
            make_btn("0: Back to Kernel Dashboard", "0"),
        ], padding=4, align=WindowAlign.CENTER)

        # Main static content
        static_content = FormattedTextControl(text=self.render_rich_content)
        
        theme = USER_PREFS.get("theme", "industrial")
        footer_label = " [bold cyan]🖱️ Mouse Active[/bold cyan]" if theme != "claude" else " [bold white]❯[/bold white] [dim]Select Option[/dim]"

        root_container = HSplit([
            Window(content=static_content, wrap_lines=True),
            HSplit([row1, row2, row3, row4, row5, row6], padding=1), # Increased padding
            Window(height=1, char=" "), # Spacer
            Box(Label(f"{footer_label} [dim]• Click any option or use Hotkeys (A, C, P...)[/dim]", style="italic"), padding=1),
        ], align=WindowAlign.CENTER)
        
        if theme in ["claude", "anthropic", "minimalist"]:
            return Layout(root_container)
        return Layout(Shadow(Box(root_container, padding=1)))

    async def run(self):
        from prompt_toolkit.styles import Style
        from prompt_toolkit.application import Application
        
        theme = USER_PREFS.get("theme", "industrial")
        focused_color = "magenta" if theme != "claude" else "cyan"

        style = Style.from_dict({
            'button': 'bold white bg:black' if theme != "claude" else 'white',
            'button.focused': f'bold white bg:{focused_color}' if theme != "claude" else 'bold cyan underline',
            'button.text': 'white',
            'label': 'bold cyan',
            'frame.label': 'bold magenta',
            'shadow': 'bg:gray',
        })
        
        app = Application(
            layout=self.get_layout(),
            key_bindings=self.kb,
            style=style,
            mouse_support=True,
            full_screen=True
        )
        await app.run_async()
        return self.result

async def get_interactive_choice(active_agents):
    app = InteractiveSwarmApp(active_agents)
    return await app.run()
