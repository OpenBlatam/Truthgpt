import typer
import asyncio
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import console

async def async_swarm_ask(prompt: str, user_id: str = "cli_user", stream: bool = False, engine: str = "deepseek"):
    from optimization_core.agents.client import AgentClient
    from optimization_core.agents.engines import engine_registry
    llm = engine_registry.get_engine(engine)
    client = AgentClient(use_swarm=True, llm_engine=llm)
    from .core import get_theme_color, get_theme_panel
    color = get_theme_color()
    with Progress(SpinnerColumn(style=color), TextColumn(f"[bold {color}]" + "{task.description}")) as progress:
        task = progress.add_task("Routing to experts...", total=None)
        response = await client.run(user_id=user_id, prompt=prompt, return_response=True)
        progress.update(task, description="Response received")
    from optimization_core.agents.models import AgentResponse
    if not isinstance(response, AgentResponse):
        content, agent_name, action_type = str(response), "Swarm", "final_answer"
    else:
        content = response.content
        agent_name = response.metadata.get('agent') or response.metadata.get('routed_to') or "Swarm"
        action_type = response.action_type
    console.print(get_theme_panel(content, title=f"🤖 {agent_name}"))
    if action_type == "approval_required": console.print("[yellow]⚠️  HITL: Aprobación requerida en la API.[/yellow]")

def register_swarm_commands(app: typer.Typer):
    @app.command(name="ask")
    def swarm_ask(
        prompt: str = typer.Argument(..., help="Query for the agent swarm"),
        user_id: str = typer.Option("cli_user", "--user", "-u", help="User ID for memory context"),
        stream: bool = typer.Option(False, "--stream", "-s", help="Enable streaming output"),
        engine: str = typer.Option("deepseek", "--engine", "-e", help="LLM Engine to use")
    ):
        """Ask the agent swarm a question."""
        asyncio.run(async_swarm_ask(prompt, user_id, stream, engine))

    @app.command(name="agents")
    def swarm_list_agents():
        """List all agents registered in the swarm."""
        from optimization_core.agents.client import AgentClient
        client = AgentClient(use_swarm=True)
        table = Table(title="🐝 Active Swarm Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="green")
        if hasattr(client.swarm, "agents"):
            for name, agent in client.swarm.agents.items(): table.add_row(name, getattr(agent, "role", "Agent"))
        console.print(table)
