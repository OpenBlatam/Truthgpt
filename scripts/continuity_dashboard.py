"""
TruthGPT Continuity Dashboard — TUI Edition.
Real-time monitoring of persistent tasks and cloud offloading.
"""

import asyncio
import psutil
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.columns import Columns
from rich import box

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from modules.persistence.task_manager import get_persistence_manager, settings

console = Console()

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="side", ratio=1),
    )
    return layout

class Header:
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[bold #00FFAA]TRUTHGPT[/] [bold white]CONTINUITY ENGINE[/] [dim]v5.9 PLATINUM[/]",
            f"[bold cyan]{datetime.now().strftime('%H:%M:%S')}[/]",
        )
        return Panel(grid, style="white on #111111", border_style="#00FFAA", box=box.ROUNDED)

class SystemStats:
    def __rich__(self) -> Panel:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim", justify="right")
        table.add_column(style="bold cyan")
        
        table.add_row("CPU NODE:", f"{cpu}%")
        table.add_row("RAM ADAPT:", f"{ram}%")
        table.add_row("SWARM LINK:", "[bold green]ONLINE[/]" if settings.remote_url else "[dim]LOCAL ONLY[/]")
        table.add_row("ENCRYPTION:", "[bold yellow]AES-256[/]")
        
        return Panel(table, title="[bold white]Node Telemetry[/]", border_style="bright_blue", box=box.ROUNDED)

async def get_task_table():
    tasks = await get_persistence_manager().list_active_tasks()
    
    table = Table(box=box.SIMPLE_HEAVY, expand=True, header_style="bold #00FFAA")
    table.add_column("Expert ID", style="cyan", no_wrap=True)
    table.add_column("Agent Prototype", style="bold white")
    table.add_column("Step", justify="right", style="magenta")
    table.add_column("Stability", justify="center")
    table.add_column("Mental Sync", style="dim")

    for task in tasks:
        status_text = "[bold green]ACTIVE[/]" if task.status == "running" else "[bold yellow]OFFLOADED[/]"
        table.add_row(
            f"TX-{task.task_id[:8]}",
            f"🤖 {task.agent_name}",
            str(task.iteration),
            status_text,
            task.timestamp.split("T")[1][:8],
        )
    
    if not tasks:
        return Panel("[dim]No persistent agent missions active in the current matrix.[/]", title="[bold white]Active Swarm Threads[/]", border_style="#00FFAA", box=box.ROUNDED)
        
    return Panel(table, title="[bold white]Active Swarm Threads[/]", border_style="#00FFAA", box=box.ROUNDED)

async def run_dashboard():
    layout = make_layout()
    layout["header"].update(Header())
    layout["footer"].update(Panel(f"Continuity Tunnel: [cyan]{settings.remote_url or 'LOCALHOST'}[/] | [dim]Monitoring persistent mental states across swarm nodes.[/]", style="white on #111111", border_style="dim"))

    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            layout["header"].update(Header())
            layout["side"].update(SystemStats())
            layout["main"].update(await get_task_table())
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        pass
