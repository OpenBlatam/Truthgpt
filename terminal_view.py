# terminal_view.py
"""
Integrated Terminal View for TruthGPT using Rich.
Displays agent reasoning and workflow execution logs side-by-side.
"""

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text
from rich.logging import RichHandler
import logging
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class LiveTerminal:
    """ Terminal interactiva basada en Rich para monitoreo continuo. """
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.layout = self._make_layout()
        self.live = Live(self.layout, console=self.console, refresh_per_second=4,
                         screen=True, vertical_overflow="visible")
        self.agent_header = "Agent Status: Initializing..."
        self.agent_logs: List[str] = []
        self.workflow_logs: List[str] = []
        self.current_thought = ""
        self.live_task = None

    def _make_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="agent_panel", ratio=2),
            Layout(name="workflow_panel", ratio=3)
        )
        return layout

    def update_header(self, text: str = None, style: str = "bold cyan"):
        """Actualiza el panel superior."""
        if text:
            self.agent_header = text
        self.layout["header"].update(
            Panel(Text(self.agent_header, style=style), style="cyan")
        )

    def add_agent_log(self, message: str):
        """Añade una línea al panel de razonamiento del agente."""
        timestamp = time.strftime("%H:%M:%S")
        self.agent_logs.append(f"[{timestamp}] {message}")
        self._refresh_agent_panel()

    def update_thought(self, thought: str):
        """Actualiza el pensamiento actual (p.ej., reasoning del LLM)."""
        self.current_thought = thought
        self._refresh_agent_panel()

    def add_workflow_log(self, message: str, style: str = ""):
        """Añade una entrada al panel de ejecución de flujo."""
        timestamp = time.strftime("%H:%M:%S")
        self.workflow_logs.append(f"[{timestamp}] {message}")
        self._refresh_workflow_panel()

    def _refresh_agent_panel(self):
        content = []
        if self.current_thought:
            content.append(f"[bold yellow]Thought:[/bold yellow] {self.current_thought}\n")
        for log in self.agent_logs[-15:]:
            content.append(log)
        panel = Panel("\n".join(content), title="Agent Reasoning", border_style="yellow")
        self.layout["agent_panel"].update(panel)

    def _refresh_workflow_panel(self):
        panel = Panel("\n".join(self.workflow_logs[-20:]), title="Workflow Execution", border_style="green")
        self.layout["workflow_panel"].update(panel)

    def start(self):
        """Inicia el contexto en vivo."""
        self.live.start(refresh=True)

    def stop(self):
        """Detiene el contexto."""
        self.live.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
