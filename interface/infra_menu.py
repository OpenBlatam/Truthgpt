"""
Infrastructure & Node Hub
"""
import time
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from interface.core import (
    console, clear_screen, get_header, wait_for_user
)

async def infrastructure_menu():
    while True:
        clear_screen()
        console.print(get_header())
        table = Table(title="🖥️ Local Infrastructure & Node Hub", border_style="bold cyan", expand=True)
        table.add_row("1", "Agentic PC Control", "Shell Access")
        table.add_row("0", "Back", "")
        console.print(Panel(table, border_style="cyan"))
        choice = Prompt.ask("Selection", choices=["0", "1"])
        if choice == "0": break
        elif choice == "1":
            cmd = Prompt.ask("Enter Shell Command")
            console.print(f"[cyan]Executing: {cmd}...[/cyan]")
            time.sleep(1)
        wait_for_user(force=True)

async def task_registry_menu():
    while True:
        clear_screen()
        console.print(get_header())
        table = Table(title="📜 System Task Registry")
        table.add_row("1", "View Active Tasks")
        table.add_row("0", "Back")
        console.print(table)
        choice = Prompt.ask("Selection", choices=["0", "1"])
        if choice == "0": break
        wait_for_user(force=True)
