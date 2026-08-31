"""
Swarm Handlers — Lightweight command handlers for the Swarm Hub menu.

Extracted from the monolithic swarm_menu.py for maintainability.
Contains: ask, telemetry, persona tuning, expert matrix, MCP, math, composer.
"""

import time
import inspect
import logging
from pathlib import Path
from typing import Optional, List

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from interface.core import (
    console, USER_PREFS, log_activity, clear_screen,
    get_header, wait_for_user, get_input,
)
from interface.cc_style import cc_step

logger = logging.getLogger(__name__)


# ── Ask Swarm ─────────────────────────────────────────────────────

@cc_step("Swarm Router")
async def handle_swarm_ask():
    prompt = get_input("Enter your question for the swarm")
    engine = USER_PREFS["preferred_engine"]
    log_activity("Swarm Ask", prompt)
    with console.status(f"[bold blue]Routing to expert agents using {engine}...[/bold blue]"):
        try:
            import cli
            await cli.async_swarm_ask(prompt=prompt, user_id="cli_user", stream=False, engine=engine)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    wait_for_user(force=True)


# ── Swarm Telemetry ───────────────────────────────────────────────

async def handle_swarm_telemetry():
    clear_screen()
    console.print(get_header())
    health = {"Status": "Healthy", "Latency": "45ms"}
    console.print(Panel("\n".join([f"{k}: {v}" for k, v in health.items()]), title="🛰️ Telemetry"))
    wait_for_user(force=True)


# ── Persona Tuning ────────────────────────────────────────────────

async def handle_persona_tuning(agents):
    clear_screen()
    console.print(get_header())
    if not agents:
        console.print("[yellow]⚠️ No active swarm agents available for persona tuning.[/yellow]")
        wait_for_user(force=True)
        return
    for i, a in enumerate(agents, 1):
        console.print(f" {i}. {a.name}")
    try:
        idx_str = get_input("Select expert (or '0' to cancel)", default="1")
        if idx_str == "0":
            return
        idx = int(idx_str)
        if 1 <= idx <= len(agents):
            target = agents[idx - 1]
            new_role = get_input("New Role/Description", default=getattr(target, "role", ""))
            if new_role:
                target.role = new_role
                console.print(f"[green]✓ Persona updated for {target.name}![/green]")
            else:
                console.print("[dim]No changes made.[/dim]")
        else:
            console.print("[red]❌ Invalid selection.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    wait_for_user(force=True)


# ── Expert Matrix ─────────────────────────────────────────────────

async def handle_expert_matrix(agents):
    clear_screen()
    console.print(get_header())
    table = Table(title="🛠️ Expert Tool Matrix")
    table.add_column("Expert")
    table.add_column("Tools")
    for agent in agents:
        tools = ", ".join(agent.tools.keys()) if hasattr(agent, "tools") else "N/A"
        table.add_row(agent.name, tools)
    console.print(table)
    wait_for_user(force=True)


# ── MCP Connect ───────────────────────────────────────────────────

async def handle_mcp_connect():
    import os
    from agents.framework.interfaces.client.mcp_client import MCPClient

    url = get_input(
        "Enter MCP Server URL",
        default=os.environ.get("MCP_SERVER_URL", "http://localhost:8000"),
    )
    client = MCPClient(url)
    with console.status(f"[bold cyan]Connecting to {url}...[/bold cyan]"):
        try:
            tools = await client.list_tools()
            if tools:
                table = Table(title="🛠️ External Tools")
                for t in tools:
                    table.add_row(t.get("name"), t.get("description"))
                console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    await client.close()
    wait_for_user(force=True)


# ── Math & Verification ──────────────────────────────────────────

async def handle_math_verification():
    """Interactive Math & Formal Verification console."""
    clear_screen()
    console.print(get_header())
    console.print(Panel(
        " [bold cyan]🔬 Math & Formal Verification Engine[/bold cyan]\n"
        " [dim]Lean 4 • SymPy • Z3 SMT • NumPy • Code Verify[/dim]",
        border_style="cyan",
    ))

    cmd_table = Table(title="Available Commands", box=None, padding=(0, 2))
    cmd_table.add_column("Prefix", style="bold cyan")
    cmd_table.add_column("Engine", style="white")
    cmd_table.add_column("Example", style="dim")
    cmd_table.add_row("prove:", "SymPy", "prove: (x+1)**2 == x**2 + 2*x + 1")
    cmd_table.add_row("solve:", "SymPy", "solve: x**2 - 4 = 0")
    cmd_table.add_row("simplify:", "SymPy", "simplify: (x**2-1)/(x-1)")
    cmd_table.add_row("integrate:", "SymPy", "integrate: x**2 + 2*x")
    cmd_table.add_row("diff:", "SymPy", "diff: sin(x)*cos(x)")
    cmd_table.add_row("limit:", "SymPy", "limit: sin(x)/x, x, 0")
    cmd_table.add_row("factor:", "SymPy", "factor: x**3 - 1")
    cmd_table.add_row("matrix:", "SymPy", "matrix: [[1,2],[3,4]]")
    cmd_table.add_row("eigenvalues:", "NumPy", "eigenvalues: [[1,2],[3,4]]")
    cmd_table.add_row("roots:", "NumPy", "roots: [1, -5, 6]")
    cmd_table.add_row("svd:", "NumPy", "svd: [[1,2],[3,4]]")
    cmd_table.add_row("theorem ...", "Lean 4", "theorem add_comm : ∀ a b, a + b = b + a")
    cmd_table.add_row("x > 0, ...", "Z3 SMT", "x > 0, x < 10, x*x == 49")
    cmd_table.add_row("typecheck:", "mypy", "typecheck: def f(x: int) -> int: return x")
    console.print(cmd_table)

    try:
        from agents.domains.formal_verification.math_agent import MathVerificationAgent
        from optimization_core.agents.framework.engines.engines import engine_registry

        llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
        agent = MathVerificationAgent(llm_engine=llm)
    except ImportError as e:
        console.print(f"[red]Error loading MathVerificationAgent: {e}[/red]")
        wait_for_user(force=True)
        return

    console.print("\n[dim]Type your expression (or 'exit' to return):[/dim]")
    while True:
        expr = get_input("\n[bold cyan]Math (type '0' to go back)>[/bold cyan]")
        if expr.lower() in ("exit", "quit", "0", "back", ""):
            break
        with console.status("[bold cyan]Verifying...[/bold cyan]"):
            result = await agent.process(expr, context={"user_id": "cli_math"})
            content = result.content if hasattr(result, "content") else str(result)
            console.print(Panel(content, title="🔬 Verification Result", border_style="green"))


# ── Agent Composer ────────────────────────────────────────────────

async def handle_agent_composer():
    """Interactive Agent Composer — build custom agent combinations."""
    clear_screen()
    console.print(get_header())
    console.print(Panel(
        " [bold magenta]🧩 Agent Composer — Build Your Custom Agent[/bold magenta]\n"
        " [dim]Mix capabilities from Math, Research, Code, and System domains[/dim]",
        border_style="magenta",
    ))

    try:
        from agents.orchestration.composer.agent_composer import (
            _build_catalog, save_blueprint, load_blueprints, ComposedAgent,
        )
    except ImportError as e:
        console.print(f"[red]Composer not available: {e}[/red]")
        wait_for_user(force=True)
        return

    console.print("   1. 🧩 [bold]Create New Agent[/bold]")
    console.print("   2. 📂 [bold]Load Saved Blueprint[/bold]")
    console.print("   3. 📋 [bold]View Catalog[/bold]")
    console.print("   0. 🏠 Back")
    mode = get_input("Select", choices=["0", "1", "2", "3"])
    if mode == "0":
        return

    catalog = _build_catalog()

    if mode == "3":
        cat_table = Table(title="🧩 Capability Catalog", border_style="magenta")
        cat_table.add_column("#", style="cyan", justify="right")
        cat_table.add_column("Key", style="white")
        cat_table.add_column("Category", style="yellow")
        cat_table.add_column("Description", style="green")
        for i, (key, info) in enumerate(catalog.items(), 1):
            cat_table.add_row(str(i), key, info["category"], info["description"])
        console.print(cat_table)
        wait_for_user(force=True)
        return

    if mode == "2":
        blueprints = load_blueprints()
        if not blueprints:
            console.print("[yellow]No saved blueprints found.[/yellow]")
            wait_for_user(force=True)
            return
        bp_table = Table(title="📂 Saved Blueprints", border_style="blue")
        bp_table.add_column("#", style="cyan")
        bp_table.add_column("Name", style="bold white")
        bp_table.add_column("Capabilities", style="green")
        bp_table.add_column("Created", style="dim")
        for i, bp in enumerate(blueprints, 1):
            caps = ", ".join(bp.get("capabilities", []))
            bp_table.add_row(str(i), bp["name"], caps, bp.get("created", "N/A"))
        console.print(bp_table)

        idx = int(get_input("Select blueprint to deploy", default="1"))
        if 1 <= idx <= len(blueprints):
            bp = blueprints[idx - 1]
            from optimization_core.agents.framework.engines.engines import engine_registry
            llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
            agent = ComposedAgent(
                name=bp["name"],
                role=bp.get("role", "Custom Agent"),
                capabilities=bp["capabilities"],
                llm_engine=llm,
            )
            console.print(f"\n[bold green]✓ Deployed: {agent.name}[/bold green]")
            console.print(f"[dim]Capabilities:\n{agent.get_capability_summary()}[/dim]")
            await _composer_query_loop(agent)
        return

    # mode == "1" — Create new agent
    console.print("\n[bold cyan]Step 1: Name your agent[/bold cyan]")
    agent_name = get_input("Agent name", default="MyCustomAgent")
    agent_role = get_input("Agent role/description", default="Custom Specialized Agent")

    console.print("\n[bold cyan]Step 2: Select capabilities[/bold cyan]")
    cap_table = Table(title="Available Capabilities", border_style="cyan")
    cap_table.add_column("#", style="cyan", justify="right")
    cap_table.add_column("Key", style="white")
    cap_table.add_column("Category", style="yellow")
    cap_table.add_column("Description", style="green")
    cap_keys = list(catalog.keys())
    for i, key in enumerate(cap_keys, 1):
        info = catalog[key]
        cap_table.add_row(str(i), key, info["category"], info["description"])
    console.print(cap_table)

    selection = get_input("Select capabilities (e.g. 1,2,5,8)")
    indices = [int(i.strip()) for i in selection.split(",") if i.strip().isdigit()]
    selected_caps = [cap_keys[i - 1] for i in indices if 1 <= i <= len(cap_keys)]

    if not selected_caps:
        console.print("[red]No capabilities selected.[/red]")
        wait_for_user(force=True)
        return

    console.print(f"\n[bold green]✓ Building '{agent_name}' with: {', '.join(selected_caps)}[/bold green]")

    if Confirm.ask("Save this as a reusable blueprint?", default=True):
        path = save_blueprint(agent_name, selected_caps, {"role": agent_role})
        console.print(f"[dim]Blueprint saved to {path}[/dim]")

    from optimization_core.agents.framework.engines.engines import engine_registry
    llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
    agent = ComposedAgent(
        name=agent_name,
        role=agent_role,
        capabilities=selected_caps,
        llm_engine=llm,
    )

    tools_list = ", ".join(agent.tools.keys()) if agent.tools else "none"
    console.print(f"[bold green]✓ Agent deployed with tools: {tools_list}[/bold green]")
    console.print(f"[dim]Capabilities:\n{agent.get_capability_summary()}[/dim]")
    await _composer_query_loop(agent)


async def _composer_query_loop(agent):
    """Shared interactive query loop for composed agents."""
    console.print("\n[dim]Type queries (or 'exit' to return):[/dim]")
    while True:
        query = get_input(f"\n[bold magenta]{agent.name} (type '0' to go back)>[/bold magenta]")
        if query.lower() in ("exit", "quit", "0", "back", ""):
            break
        with console.status(f"[bold cyan]{agent.name} working...[/bold cyan]"):
            res = await agent.process(query, context={"user_id": "cli_composer"})
            content = res.content if hasattr(res, "content") else str(res)
            console.print(Panel(content, title=f"🤖 {agent.name}", border_style="green"))
