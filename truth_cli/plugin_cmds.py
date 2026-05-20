import typer
from rich.table import Table
from rich.panel import Panel

from .core import console

def register_plugin_commands(app: typer.Typer):

    @app.command(name="list")
    def plugins_list():
        """List all dynamically discovered plugins and registered tools."""
        from optimization_core.agents.registry import registry
        tools = registry.get_all_tools()
        table = Table(title="[Plugin] Registered Tools & Plugins")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Source", style="green")
        table.add_column("Description", style="white")
        for name, tool in tools.items():
            if not isinstance(name, str): continue
            source = "Plugin" if "plugins" in str(getattr(tool, "__module__", "")) else "Built-in"
            desc_obj = getattr(tool, "description", "No description")
            desc_text = "N/A" if not isinstance(desc_obj, str) else ((desc_obj[:75] + "...") if len(desc_obj) > 75 else desc_obj)
            table.add_row(name, source, desc_text)
        console.print(table)

    @app.command(name="info")
    def plugins_info(name: str = typer.Argument(..., help="Tool name")):
        """Show detailed information for a specific tool or plugin."""
        from optimization_core.agents.registry import registry
        tool = registry.get_tool(name)
        if not tool:
            console.print(f"[red]✗ Tool not found: {name}[/red]")
            return
        console.print(Panel(f"[bold]Name:[/bold] {tool.name}\n[bold]Description:[/bold] {tool.description}\n[bold]Requires Approval:[/bold] {'Yes' if tool.requires_approval else 'No'}\n[bold]Class:[/bold] {type(tool).__name__}", title=f"🔌 Tool Info: {name}", border_style="cyan"))
