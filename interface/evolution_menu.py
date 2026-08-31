"""
🧬 System Evolution Engine - Autonomous Self-Modification Layer
"""
from __future__ import annotations

import asyncio
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from interface.core import (
    USER_PREFS,
    clear_screen,
    console,
    get_header,
    log_activity,
    wait_for_user,
)
from interface.registry import MenuRegistry


@MenuRegistry.register("system_evolution", title="System Evolution Engine", category="Evolution")
async def handle_system_evolution() -> None:
    """
    Main entry point for the System Evolution engine.
    Allows the user to request changes to the codebase.
    """
    clear_screen()
    console.print(get_header())
    console.print(
        Panel(
            " [bold magenta]🧬 System Evolution Engine — Autonomous Self-Modification[/bold magenta]\n"
            " [dim]Proactively modifies TruthGPT code, menus, and functions based on your queries.[/dim]",
            border_style="magenta",
        )
    )

    console.print("[yellow]WARNING: This system allows the AI to modify its own source code.[/yellow]")
    console.print("[dim]Example: 'Add a new option to the Kernel menu that displays system uptime.'[/dim]\n")

    query = Prompt.ask("[bold magenta]Evolution Query[/bold magenta]")
    if not query or query.lower() in ("exit", "quit", "0", "back"):
        return

    if not Confirm.ask("[bold red]Are you sure you want to authorize autonomous codebase modification?[/bold red]"):
        return

    # In a real scenario, this would use CodeInterpreterAgent
    console.print("[cyan]Initiating evolution cycle...[/cyan]")
    log_activity("Evolution", f"Request: {query}")

    # Placeholder for actual evolution logic
    await asyncio.sleep(1)
    console.print("[bold green]✓ Evolution cycle simulated. (CodeInterpreterAgent required for full autonomy)[/bold green]")

    wait_for_user(force=True)
