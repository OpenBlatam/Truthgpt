# enhanced_terminal.py
"""
Claude-like Enhanced Terminal View for TruthGPT.
Displays agent reasoning (thinking steps) and workflow/tool execution logs side-by-side.
"""

import time
from typing import Optional, List

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text
from rich.table import Table
from rich.style import Style


class ClaudeLikeTUI:
    """Terminal interface mimicking Claude's reasoning display with live dual-pane view."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.layout = self._init_layout()
        self.live = Live(self.layout, console=self.console, refresh_per_second=8,
                         screen=True, vertical_overflow="visible")
        
        # Data buffers
        self.agent_thoughts: List[str] = []           # reasoning steps
        self.current_input: str = ""                  # latest user input
        self.workflow_logs: List[str] = []            # tool/action logs
        self.metrics: dict = {                        # system metrics
            "tokens_used": 0,
            "elapsed": 0.0,
            "model": "loading...",
            "temperature": 0
        }
    
    def _init_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="reasoning", ratio=2),
            Layout(name="workflow", ratio=3)
        )
        return layout
    
    def update_header(self, text: str = None):
        if text:
            header_text = Text(text, style="bold white on dark_blue")
        else:
            header_text = Text("TruthGPT · Continuous Agent · Live Reasoning", style="bold white on dark_blue")
        self.layout["header"].update(
            Panel(header_text, style="blue", border_style="bright_blue")
        )
    
    def set_user_input(self, text: str):
        self.current_input = text
    
    def add_thought(self, step: str):
        """Add an internal reasoning step, styled like Claude's 'Thinking...'."""
        timestamp = time.strftime("%H:%M:%S")
        self.agent_thoughts.append(f"[{timestamp}] {step}")
        self._refresh_reasoning_panel()
    
    def add_tool_call(self, tool_name: str, input_str: str, result: str = None):
        """Log a tool execution in the workflow panel."""
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] 🛠️ {tool_name}"
        if input_str:
            msg += f"\n       ├─ Input: {input_str}"
        if result:
            msg += f"\n       └─ Result: {result}"
        self.workflow_logs.append(msg)
        self._refresh_workflow_panel()
    
    def add_workflow_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.workflow_logs.append(f"[{timestamp}] {message}")
        self._refresh_workflow_panel()
    
    def update_metrics(self, tokens_used: int = None, elapsed: float = None,
                       model: str = None, temperature: float = None):
        if tokens_used is not None:
            self.metrics["tokens_used"] = tokens_used
        if elapsed is not None:
            self.metrics["elapsed"] = elapsed
        if model is not None:
            self.metrics["model"] = model
        if temperature is not None:
            self.metrics["temperature"] = temperature
    
    def _refresh_reasoning_panel(self):
        content = []
        if self.current_input:
            content.append(f"[bold cyan]User:[/bold cyan] {self.current_input}")
            content.append("─" * 40)
        if self.agent_thoughts:
            content.append("[bold yellow]🧠 Reasoning[/bold yellow]")
            for line in self.agent_thoughts[-10:]:  # keep last 10
                content.append(line)
        else:
            content.append("[dim]Awaiting input...[/dim]")
        
        panel = Panel(
            "\n".join(content),
            title="Agent Thinking",
            border_style="yellow",
            height=20
        )
        self.layout["reasoning"].update(panel)
    
    def _refresh_workflow_panel(self):
        content = []
        for entry in self.workflow_logs[-15:]:
            content.append(entry)
        if not content:
            content.append("[dim]No workflow actions yet.[/dim]")
        
        panel = Panel(
            "\n".join(content),
            title="⚙️ Workflow & Tools",
            border_style="green",
            height=20
        )
        self.layout["workflow"].update(panel)
    
    def _refresh_footer(self):
        m = self.metrics
        footer_text = (
            f"[bold]Tokens:[/bold] {m['tokens_used']}  |  "
            f"[bold]Time:[/bold] {m['elapsed']:.2f}s  |  "
            f"[bold]Model:[/bold] {m['model']}  |  "
            f"[bold]Temp:[/bold] {m['temperature']}"
        )
        self.layout["footer"].update(
            Panel(footer_text, style="dim cyan", border_style="grey50")
        )
    
    def start(self):
        self.update_header()
        self._refresh_reasoning_panel()
        self._refresh_workflow_panel()
        self._refresh_footer()
        self.live.start(refresh=True)
    
    def stop(self):
        self.live.stop()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def refresh(self):
        self._refresh_reasoning_panel()
        self._refresh_workflow_panel()
        self._refresh_footer()
