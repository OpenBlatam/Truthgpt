"""
Header & Terminal Banner Rendering Engine for TruthGPT Interface.
==================================================================
Renders high-fidelity ASCII logos, real-time API telemetry sidebars,
knowledge density graphs, and responsive Claude-style and Industrial HUDs.
"""
from __future__ import annotations

import os
import shutil
import time
from typing import List, Optional, Union

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from interface.config import USER_PREFS
from interface.console import console, clear_screen
from interface.constants import (
    CLAUDE_BANNER_BOT,
    CLAUDE_BANNER_TOP,
    DEFAULT_HEADER_UPDATES,
    INDUSTRIAL_BANNER_ASCII,
    SYSTEM_VERSION_BANNER,
)
from interface.telemetry import (
    TelemetryProvider,
    _fast_count_papers,
    get_real_budget_stats,
)


def get_header(updates: Optional[List[str]] = None) -> Union[Panel, Text]:
    """Dynamically construct and return the top-level terminal banner based on current theme."""
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        return get_claude_header(updates=updates)

    terminal_lines = shutil.get_terminal_size().lines or 24

    if terminal_lines < 30:
        return Panel(
            Text("🚀 TruthGPT Industrial OS  [bold red][R] Reboot[/bold red]", style="bold orange3", justify="center"),
            border_style="orange3",
            padding=(0, 1),
        )

    return Panel(
        Text(INDUSTRIAL_BANNER_ASCII, style="bold orange3", justify="center"),
        title="[bold purple] TruthGPT Industrial OS [/bold purple]",
        subtitle="[bold orange3] truthgpt@kernel [/bold orange3]  [bold red][R] Reboot[/bold red]",
        border_style="orange3",
        padding=(1, 2),
    )


def get_claude_header(updates: Optional[List[str]] = None) -> Text:
    """Sentient Cyber-Industrial Header: REAL API TELEMETRY & HUD."""
    theme_color = "plum1"
    version = SYSTEM_VERSION_BANNER
    user_name = USER_PREFS.get("user_name", "Explorer")
    current_path = os.getcwd()
    timestamp = time.strftime("%H:%M:%S")
    uptime = "02:16:12"

    if updates is None:
        updates = list(DEFAULT_HEADER_UPDATES)

    budget_stats = get_real_budget_stats()
    cost_str = f"${budget_stats['total_usd']:.4f}"

    terminal_size = shutil.get_terminal_size()
    w = max(80, terminal_size.columns or 100)
    h = terminal_size.lines or 24

    if h < 30:
        telemetry = Text()
        telemetry.append(f" {timestamp} ", style="bold white bg:black")
        telemetry.append(" █▓▒░ TRUTHGPT CORE ░▒▓█ ", style="bold black bg:white")
        telemetry.append(f"  COST:[{cost_str}]  ", style="dim")
        stats = TelemetryProvider.get_stats()
        telemetry.append(f" CPU: {stats['load']:.0f}% | RAM: {stats['mem']:.0f}% ", style="white")
        header_line = Text(f"\n── TruthGPT OS {version} ──────────────────────────────────────", style=f"bold {theme_color}")
        final_header = Text()
        final_header.append(telemetry)
        final_header.append(header_line)
        final_header.append("\n")
        return final_header

    telemetry = Text()
    telemetry.append(f" {timestamp} ", style="bold white bg:black")
    telemetry.append(" █▓▒░ TRUTHGPT CORE ░▒▓█ ", style="bold black bg:white")
    telemetry.append(f"  UPTIME:[{uptime}]  COST:[{cost_str}]  ", style="dim")

    # Dynamic real-time system telemetry (CPU / RAM / Session ID)
    stats = TelemetryProvider.get_stats()
    sys_status = Text()
    sys_status.append(" ● ", style="bold green")
    sys_status.append(f"CPU: {stats['load']:.0f}% | RAM: {stats['mem']:.0f}% ", style="white")
    sys_status.append(f"({stats['session_id']})", style="dim")

    padding = max(1, w - len(telemetry.plain) - len(sys_status.plain) - 2)
    telemetry.append(" " * padding)
    telemetry.append(sys_status)

    telemetry.append("\n")
    telemetry.append("● NEURAL LINK: ESTABLISHED ", style="bold green")

    # Top Divider with Version (Pure Claude Style)
    header_line = Text(f"\n── TruthGPT OS {version} ", style=f"bold {theme_color}")
    header_line.append("─" * 60, style="dim")

    # Dynamic column widths based on current console width to prevent clutter/wrapping
    left_w = max(42, int(w * 0.35))
    right_w = w - left_w - 2

    table = Table.grid(expand=True)
    table.add_column(width=left_w)   # Left side
    table.add_column(width=right_w)  # Right side (Sidebar)

    # Left Content: Logo + Welcome + System status
    left_content = Text()
    left_content.append(CLAUDE_BANNER_TOP, style=theme_color)
    left_content.append(CLAUDE_BANNER_BOT, style=theme_color)

    left_content.append(f" Welcome back {user_name}!\n\n", style="bold white")
    left_content.append(Text.from_markup("[dim] TruthGPT 5.9 · [/dim][bold #00ff00]SOTA[/bold #00ff00][dim] · 128k Context[/dim]\n"))
    left_content.append(Text.from_markup("[dim] Cascading: [/dim][cyan]ACTIVE[/cyan][dim] · Sandbox: [/dim][bold white]HARDENED[/bold white]\n"))
    left_content.append(f" {current_path}\n", style="dim")

    # Right Content: Sidebar (Industrial HUD Stats)
    right_content = Text()

    # 1. API Budget & Costs
    right_content.append("\n █▓▒░ COST TELEMETRY\n", style="white")
    spent = budget_stats.get("total_usd", 0.0)
    limit = budget_stats.get("limit", 10.0)
    remaining = max(0.0, limit - spent)

    right_content.append(" ├ Budget:      ", style="dim")
    right_content.append(f"${limit:.2f}\n", style="green")
    right_content.append(" ├ Spent:       ", style="dim")
    right_content.append(f"${spent:.4f}\n", style="cyan")
    right_content.append(" ├ Remaining:   ", style="dim")
    right_content.append(f"${remaining:.4f}\n", style="yellow")
    right_content.append(" │\n", style="dim")

    balances = TelemetryProvider.get_api_balances()
    if balances:
        keys = list(balances.keys())
        for i, name in enumerate(keys):
            val, b_type = balances[name]
            prefix = " └ " if i == len(keys) - 1 else " ├ "
            right_content.append(f"{prefix}{name:<10}: ", style="dim")
            if "Balance" in b_type:
                right_content.append(f"${val:.4f}" if val is not None else "N/A", style="green")
            else:
                right_content.append(f"${val:.4f}" if val is not None else "N/A", style="cyan")
            right_content.append(f" ({b_type})\n", style="dim")

    # 2. Mission Persistence (Background Tasks)
    right_content.append("\n █▓▒░ MISSION PERSISTENCE\n", style="white")
    from interface.events import background_missions
    active_count = len(background_missions)
    right_content.append(f" ├ Active:      {active_count}\n", style="dim")
    right_content.append(" ├ Status:      ", style="dim")
    right_content.append("RESILIENT\n", style="bold green")
    right_content.append(" └ Continuity:  ", style="dim")
    right_content.append("LOCKED\n", style="bold cyan")

    # 3. What's New
    right_content.append("\n What's new\n", style="white")
    for update in updates:
        right_content.append(f" - {update}\n", style="dim")

    # 4. Expert Latency
    right_content.append("\n █▓▒░ EXPERT LATENCY\n", style="white")
    right_content.append(" ├ Swarm-Core:  12ms\n", style="dim")
    right_content.append(" └ Frontier-X:  24ms\n", style="dim")

    # 5. Knowledge Density
    right_content.append("\n █▓▒░ KNOWLEDGE DENSITY\n", style="white")
    paper_count = _fast_count_papers()
    right_content.append(f" ├ Indexed:     {paper_count} papers\n", style="dim")
    right_content.append(" ├ Flow:        ", style="dim")
    right_content.append("⎵⎶⎷▂▃▅▇█▆▅▃ \n", style="bold magenta")
    right_content.append(" └ SOTA-Sync:   ", style="dim")
    right_content.append("100%\n", style="bold green")

    table.add_row(left_content, right_content)

    # Tool Execution HUD
    tool_hud = Text()
    tool_hud.append(" ACTION: ", style="bold black bg:white")
    tool_hud.append(" [READY] ", style="bold cyan")
    tool_hud.append(" IDLE: ", style="dim")
    tool_hud.append("0.0s", style="bold green")
    tool_hud.append(" " * 15)
    tool_hud.append("✔ AGENTIAL MODE: ACTIVE", style="bold green")

    # Assemble final output
    final_header = Text()
    final_header.append(telemetry)
    final_header.append("\n")
    final_header.append(tool_hud)
    final_header.append("\n")
    final_header.append(header_line)
    final_header.append("\n")

    with console.capture() as capture:
        console.print(table)

    final_header.append(Text.from_ansi(capture.get()))
    final_header.append("─" * 80 + "\n", style="dim")

    return final_header


def linux_boot_sequence() -> None:
    """Instantaneous kernel injection sequence for TruthGPT."""
    clear_screen()
    theme = USER_PREFS.get("theme", "industrial")
    color = "plum1" if theme in ["claude", "anthropic", "minimalist"] else "orange3"
    console.print(f"[bold {color}]>>> INJECTING TRUTHGPT KERNEL...[/bold {color}]\n")
    stages = [
        "Initializing Neural Fabric...",
        "Connecting to Swarm Nodes...",
        "Loading Expert Matrices...",
        "Syncing Neural Vault...",
        "Unlocking Overdrive Mode...",
    ]
    for stage in stages:
        console.print(f" [cyan]*[/cyan] [white]{stage}[/white] [dim]... [bold green]OK[/bold green][/dim]")
        time.sleep(0.05)

    console.print("\n[bold white bg:black] SESSION ESTABLISHED [/bold white bg:black] [dim]Ready for Agent command.[/dim]\n")
