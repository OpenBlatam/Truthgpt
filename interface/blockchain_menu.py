"""
Blockchain & Web3 Hub - Layer 9
"""
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from interface.core import (
    console, USER_PREFS, clear_screen, get_header, wait_for_user, BLOCKCHAIN_READY
)

async def blockchain_menu():
    while True:
        clear_screen()
        console.print(get_header())
        console.print(f" [bold yellow]Blockchain & Web3 Hub:[/bold yellow] [dim]Layer 9 Integrated[/dim]")
        table = Table(show_header=False, box=None)
        table.add_row("1", "Wallet Info")
        table.add_row("2", "Smart Contract Audit")
        table.add_row("0", "Back")
        console.print(table)
        
        choice = Prompt.ask("Selection", choices=["0", "1", "2"])
        if choice == "0": break
        
        if not BLOCKCHAIN_READY:
            console.print("[red]Error: Blockchain modules not found.[/red]")
        else:
            # ... logic from main.py ...
            console.print("[cyan]Querying blockchain...[/cyan]")
        wait_for_user(force=True)
