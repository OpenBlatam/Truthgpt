import typer
import asyncio
from rich.console import Console
from rich.table import Table
from modules.persistence.task_manager import get_persistence_manager, settings

app = typer.Typer(help="⏳ Manage persistent agent tasks and system continuity.")
console = Console()

@app.command("list")
def list_tasks():
    """List all active persistent tasks."""
    async def _list():
        pm = get_persistence_manager()
        tasks = await pm.list_active_tasks()
        
        if not tasks:
            console.print("[yellow]No active persistent tasks found.[/]")
            return
            
        table = Table(title="TruthGPT Persistent Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Agent", style="magenta")
        table.add_column("User", style="green")
        table.add_column("Iteration", justify="right")
        table.add_column("Status", justify="center")
        
        for t in tasks:
            status_style = "bold green" if t.status == "running" else "bold yellow"
            table.add_row(t.task_id[:12], t.agent_name, t.user_id, str(t.iteration), f"[{status_style}]{t.status.upper()}[/]")
            
        console.print(table)
        
    asyncio.run(_list())

@app.command("resume")
def resume_task(task_id: str):
    """Manually resume a specific task."""
    async def _resume():
        from agents.razonamiento_planificacion.orchestrator import MultiUserReActAgent
        from agents.models import AgentConfig
        from agents.engines import engine_registry
        
        llm = engine_registry.get_engine("deepseek") or engine_registry.get_engine("google")
        agent = MultiUserReActAgent(config=AgentConfig(llm_engine=llm, persistent=True))
        
        console.print(f"[bold cyan]Resuming task {task_id}...[/]")
        response = await agent.resume_task(task_id)
        console.print(f"\n[bold green]Final Answer:[/]\n{response.content}")
        
    asyncio.run(_resume())

@app.command("dashboard")
def show_dashboard():
    """Launch the real-time continuity dashboard."""
    from scripts.continuity_dashboard import run_dashboard
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        pass

@app.command("offload")
def cloud_offload():
    """Emergency sync all tasks to the cloud swarm node."""
    async def _offload():
        pm = get_persistence_manager()
        if not settings.remote_url:
            console.print("[bold red]Error:[/] No remote swarm node configured. Set TRUTHGPT_REMOTE_URL.")
            return
            
        console.print("[bold yellow]Initiating emergency cloud offload...[/]")
        await pm.sync_all_to_cloud()
        console.print("[bold green]Success:[/] All tasks synchronized to cloud node.")
        
    asyncio.run(_offload())

def register_continuity_commands(parent_app: typer.Typer):
    parent_app.add_typer(app, name="continuity")
