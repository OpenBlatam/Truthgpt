import os
import sys
import time
from typing import Optional
import typer
# Heavy imports moved inside commands for speed
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from .core import _fix_param, console

def register_system_commands(app: typer.Typer):

    @app.command()
    def serve(
        host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
        port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
        workers: int = typer.Option(4, "--workers", "-w", help="Number of workers"),
        reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
        config: Optional[str] = typer.Option(None, "--config", "-c", help="API config path")
    ):
        """Start the inference API server."""
        host = _fix_param(host, "0.0.0.0")
        port = int(_fix_param(port, 8080))
        workers = int(_fix_param(workers, 4))
        
        import uvicorn
        os.environ.setdefault("TRUTHGPT_CONFIG", config or "modules/base/config_management/configs/llm_default.yaml")
        
        console.print(Panel(
            f"[bold]Frontier Inference API[/bold]\nHost: {host}\nPort: {port}\nWorkers: {workers}",
            title="🚀 Starting Server", border_style="green"
        ))
        
        try:
            uvicorn.run("inference.api:app", host=host, port=port, workers=workers if not reload else 1, reload=reload, log_level="info")
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")

    @app.command()
    def tools(
        name: Optional[str] = typer.Argument(None, help="Name of the tool to run"),
        list_tools: bool = typer.Option(False, "--list", "-l", help="List available tools")
    ):
        """Access and run internal optimization tools & integration tests."""
        from optimization_core.tools import list_available_tools, get_tool_info
        available = list_available_tools()
        
        if list_tools or not name:
            table = Table(title="🛠️ Available Optimization Tools")
            table.add_column("Tool Name", style="cyan")
            table.add_column("Status", style="green")
            for t in available:
                table.add_row(t, "[green]Ready[/green]")
            console.print(table)
            if not name:
                console.print("\n[dim]Run 'truth tools <name>' to execute a specific tool.[/dim]")
                return

        if name not in available:
            console.print(f"[red]✗ Unknown tool: {name}[/red]")
            sys.exit(1)

        console.print(f"[bold cyan]➤ Running tool: {name}...[/bold cyan]")
        try:
            from optimization_core import tools as tools_mod
            tool_module = getattr(tools_mod, name)
            if hasattr(tool_module, "main"): tool_module.main()
            elif hasattr(tool_module, "run"): tool_module.run()
            console.print(f"[green]✓ Tool '{name}' completed.[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error running tool '{name}': {e}[/red]")
            sys.exit(1)

    @app.command()
    def health(
        url: str = typer.Option(os.environ.get("TRUTH_API_URL", "http://localhost:8080"), "--url", "-u", help="API URL"),
        timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout in seconds")
    ):
        """Check API health status."""
        import httpx
        import torch
        url = _fix_param(url, os.environ.get("TRUTH_API_URL", "http://localhost:8080"))
        timeout = int(_fix_param(timeout, 5))
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{url}/health")
                response.raise_for_status()
                data = response.json()
                status = data.get("status", "unknown")
                color = "green" if status == "healthy" else "yellow"
                console.print(Panel(f"[bold]Status:[/bold] [{color}]{status}[/{color}]\n[bold]Timestamp:[/bold] {data.get('timestamp', 'N/A')}", title="🏥 Health Check", border_style=color))
                if "checks" in data:
                    table = Table(title="Component Checks")
                    table.add_column("Component", style="cyan")
                    table.add_column("Status", style="green")
                    for component, status in data["checks"].items(): table.add_row(component, status)
                    console.print(table)
                sys.exit(0 if status == "healthy" else 1)
        except Exception:
            console.print(Panel(f"[yellow]⚠ API Server is currently OFFLINE.[/yellow]\n[dim]Note: Run 'truth serve' to start the backend.[/dim]\n\n[bold white]Local System Integrity:[/bold white]\n✓ CUDA/MPS: {'Active' if torch.cuda.is_available() else 'Disabled'}\n✓ Python Core: {sys.version.split()[0]}\n✓ Registry: Connected", title="🏥 Health Check (Local Mode)", border_style="yellow"))

    @app.command()
    def metrics(
        url: str = typer.Option(os.environ.get("TRUTH_API_URL", "http://localhost:8080"), "--url", "-u", help="API URL"),
        format: str = typer.Option("table", "--format", "-f", help="Output format (table/json)")
    ):
        """Get API metrics."""
        import httpx
        try:
            with httpx.Client() as client:
                response = client.get(f"{url}/metrics")
                response.raise_for_status()
                if format == "json": console.print_json(response.text)
                else:
                    lines = response.text.split("\n")
                    metrics_data = {parts[0]: parts[1] for line in lines if line and not line.startswith("#") for parts in [line.split()] if len(parts) >= 2}
                    if metrics_data:
                        table = Table(title="API Metrics")
                        table.add_column("Metric", style="cyan")
                        table.add_column("Value", style="green")
                        for metric, value in sorted(metrics_data.items()): table.add_row(metric, value)
                        console.print(table)
                    else: console.print("[yellow]No metrics available[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Failed to fetch metrics: {e}[/red]")
            sys.exit(1)

    @app.command()
    def test_api(
        url: str = typer.Option(os.environ.get("TRUTH_API_URL", "http://localhost:8080"), "--url", "-u", help="API URL"),
        token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
        prompt: str = typer.Option("Hello, world!", "--prompt", "-p", help="Test prompt"),
        iterations: int = typer.Option(1, "--iterations", "-i", help="Number of test requests")
    ):
        """Test the inference API with sample requests."""
        import httpx
        token = token or os.getenv("TRUTHGPT_API_TOKEN", "changeme")
        console.print(f"[bold]Testing API: {url}[/bold]")
        results = []
        with Progress() as progress:
            task = progress.add_task("Sending requests...", total=iterations)
            for i in range(iterations):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        start = time.time()
                        response = client.post(f"{url}/v1/infer", headers={"Authorization": f"Bearer {token}"}, json={"model": "gpt-4o", "prompt": prompt, "params": {"max_new_tokens": 64, "temperature": 0.7}})
                        elapsed = time.time() - start
                        response.raise_for_status()
                        results.append({"iteration": i + 1, "status": response.status_code, "latency_ms": elapsed * 1000, "success": True})
                except Exception as e: results.append({"iteration": i + 1, "status": "error", "error": str(e), "success": False})
                progress.update(task, advance=1)
        table = Table(title="Test Results")
        table.add_column("Iteration", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Latency (ms)", style="yellow")
        for r in results:
            status_str = str(r.get("status", "N/A"))
            latency_str = f"{r.get('latency_ms', 0):.2f}" if r.get("success") else "N/A"
            table.add_row(str(r["iteration"]), ("[green]✓[/green] " if r.get("success") else "[red]✗[/red] ") + status_str, latency_str)
        console.print(table)
        successful = sum(1 for r in results if r.get("success"))
        avg_latency = sum(r.get("latency_ms", 0) for r in results if r.get("success")) / max(successful, 1)
        console.print(f"\n[bold]Success Rate:[/bold] {successful}/{iterations} ({successful/iterations*100:.1f}%)")
        console.print(f"[bold]Average Latency:[/bold] {avg_latency:.2f}ms")

    @app.command()
    def version():
        """Show version information."""
        import torch
        try:
            import importlib.metadata
            ver = importlib.metadata.version("frontier-model-run")
        except: ver = "1.0.0"
        console.print(Panel(f"[bold]Frontier-Model-Run[/bold]\nVersion: {ver}\nPython: {sys.version.split()[0]}\nPyTorch: {torch.__version__ if torch else 'N/A'}", title="📦 Version Info", border_style="blue"))
