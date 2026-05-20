"""
🛠️ CLI Tool for Frontier-Model-Run
Enhanced command-line interface with improved UX
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure') and sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import time
from pathlib import Path
import json
from typing import Optional, List

import typer
# Heavy imports moved inside commands for speed
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

try:
    from rich import print as rprint
except ImportError:
    rprint = print

from configs.loader import load_config, parse_overrides
# Heavy ML models import deferred for fast boot

app = typer.Typer(
    name="frontier",
    help="🚀 Frontier-Model-Run CLI - Enterprise ML Platform",
    add_completion=True,
    no_args_is_help=True
)
console = Console()


@app.command()
def infer(
    config: str = typer.Option("configs/llm_default.yaml", "--config", "-c", help="Configuration file"),
    text: str = typer.Argument(..., help="Input text for inference"),
    max_new_tokens: int = typer.Option(64, "--max-tokens", "-m", help="Maximum tokens to generate"),
    temperature: float = typer.Option(0.8, "--temperature", "-t", help="Sampling temperature"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (optional)"),
    override: Optional[List[str]] = typer.Option(None, "--override", "-O", help="Config overrides"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    latency_optimize: bool = typer.Option(False, "--latency-optimize", "-lo", help="Apply Chain of Draft & Elastic Reasoning to reduce tokens"),
    chain_draft_variant: str = typer.Option("baseline", "--chain-draft-variant", "-cdv", help="Chain of Draft variant (baseline, structured, code_specific)"),
    elastic_reasoning: bool = typer.Option(False, "--elastic-reasoning", "-er", help="Use Elastic Reasoning token budget"),
    t_budget: int = typer.Option(10, "--t-budget", "-tb", help="Thinking token budget for Elastic Reasoning"),
    s_budget: int = typer.Option(50, "--s-budget", "-sb", help="Solution token budget for Elastic Reasoning"),
    fp16: bool = typer.Option(False, "--fp16", "-fp", help="Enable FP16 stability for faster inference")
):
    """Run inference on text input with optional latency optimizations."""
    import torch
    from latency_optimizations import apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Loading model...", total=None)
        try:
            from models import build_model
            cfg = load_config(config, override)
            progress.update(task, description="Building model...")
            model = build_model(cfg.model.family, cfg.dict())
            
            # Apply FP16 stability
            if fp16:
                progress.update(task, description="Applying FP16 stability...")
                try:
                    model = apply_fp16_stability(model)
                    console.print("[cyan]✓ FP16 stability enabled[/cyan]")
                except Exception as e:
                    console.print(f"[yellow]⚠ FP16 conversion skipped: {e}[/yellow]")
            
            # Apply latency prompt optimizations
            optimized_text = text
            if latency_optimize:
                progress.update(task, description="Optimizing prompt with Chain of Draft...")
                optimized_text = apply_chain_of_draft(optimized_text, variant=chain_draft_variant)
                console.print(f"[cyan]✓ Chain of Draft ({chain_draft_variant}) applied[/cyan]")
            elif elastic_reasoning:
                progress.update(task, description="Applying Elastic Reasoning budgets...")
                optimized_text = apply_elastic_reasoning(optimized_text, t_budget, s_budget, wrapper=True)
                console.print(f"[cyan]✓ Elastic Reasoning (think:{t_budget}, sol:{s_budget}) applied[/cyan]")
            
            progress.update(task, description="Running inference...")
            
            start_time = time.time()
            out = model.infer({
                "text": optimized_text,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature
            })
            elapsed = time.time() - start_time
            
            result = out.get("text", "")
            
            if output:
                Path(output).write_text(result)
                console.print(f"[green]✓[/green] Output saved to {output}")
            else:
                console.print(Panel(result, title="[bold]Inference Result[/bold]", border_style="blue"))
            
            if verbose:
                usage = out.get("usage", {})
                console.print(f"\n[dim]Latency: {elapsed*1000:.2f}ms[/dim]")
                if usage:
                    console.print(f"[dim]Tokens: {usage}[/dim]")
        
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            sys.exit(1)


@app.command()
def train(config: str, override: list[str] = typer.Option(None)):
    """Train using the existing GenericTrainer and YAML config."""
    # Reuse train_llm utilities to avoid duplication
    from train_llm import to_cfg as to_trainer_cfg  # type: ignore
    from train_llm import read_yaml as read_yaml_dict  # type: ignore
    from train_llm import load_text_splits  # type: ignore
    cfg_dict = read_yaml_dict(config)
    # Apply CLI overrides on top of file config
    merged = {**cfg_dict}
    for ov in (override or []):
        # simple override merge via loader helpers
        from configs.loader import parse_overrides as _po, deep_merge as _dm
        merged = _dm(merged, _po([ov]))
    trainer_cfg = to_trainer_cfg(merged)

    data_cfg = merged.get("data", {})
    dataset = str(data_cfg.get("dataset", "wikitext"))
    subset = str(data_cfg.get("subset", "wikitext-2-raw-v1"))
    text_field = str(data_cfg.get("text_field", "text"))
    max_seq_len = int(data_cfg.get("max_seq_len", 512))
    limit = int(data_cfg.get("limit", 5000))

    from trainers.trainer import GenericTrainer  # type: ignore

    train_texts, val_texts = load_text_splits(dataset, subset, text_field, limit)
    trainer = GenericTrainer(
        cfg=trainer_cfg,
        train_texts=train_texts,
        val_texts=val_texts,
        text_field_max_len=max_seq_len,
    )
    trainer.train()
    typer.echo("Training completed. Checkpoints saved to: " + trainer_cfg.output_dir)


@app.command()
def export(checkpoint_dir: str, onnx_path: str = "model.onnx"):
    """Export a HF checkpoint directory to ONNX for fast inference."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if not os.path.isdir(checkpoint_dir):
        raise typer.BadParameter(f"Checkpoint dir not found: {checkpoint_dir}")
    tok = AutoTokenizer.from_pretrained(checkpoint_dir)
    mdl = AutoModelForCausalLM.from_pretrained(checkpoint_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mdl.to(device).eval()
    sample = tok("hello", return_tensors="pt").to(device)
    torch.onnx.export(
        mdl,
        (sample["input_ids"], sample.get("attention_mask")),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        opset_version=17,
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "logits": {0: "batch", 1: "seq"},
        },
    )
    typer.echo(f"Exported ONNX to {onnx_path}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind"),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of workers"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="API config path")
):
    """Start the inference API server."""
    import uvicorn
    
    os.environ.setdefault("TRUTHGPT_CONFIG", config or "configs/llm_default.yaml")
    
    console.print(Panel(
        f"[bold]Frontier Inference API[/bold]\n"
        f"Host: {host}\n"
        f"Port: {port}\n"
        f"Workers: {workers}",
        title="🚀 Starting Server",
        border_style="green"
    ))
    
    try:
        uvicorn.run(
            "inference.api:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")

@app.command()
def health(
    url: str = typer.Option("http://localhost:8080", "--url", "-u", help="API URL"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout in seconds")
):
    """Check API health status."""
    import httpx
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{url}/health")
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status", "unknown")
            color = "green" if status == "healthy" else "yellow"
            
            console.print(Panel(
                f"[bold]Status:[/bold] [{color}]{status}[/{color}]\n"
                f"[bold]Timestamp:[/bold] {data.get('timestamp', 'N/A')}",
                title="🏥 Health Check",
                border_style=color
            ))
            
            if "checks" in data:
                table = Table(title="Component Checks")
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                
                for component, status in data["checks"].items():
                    table.add_row(component, status)
                
                console.print(table)
            
            sys.exit(0 if status == "healthy" else 1)
    
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {e}[/red]")
        sys.exit(1)

@app.command()
def metrics(
    url: str = typer.Option("http://localhost:8080", "--url", "-u", help="API URL"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table/json)")
):
    """Get API metrics."""
    import httpx
    try:
        with httpx.Client() as client:
            response = client.get(f"{url}/metrics")
            response.raise_for_status()
            
            if format == "json":
                console.print_json(response.text)
            else:
                # Parse Prometheus format and display as table
                lines = response.text.split("\n")
                metrics_data = {}
                
                for line in lines:
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            metrics_data[parts[0]] = parts[1]
                
                if metrics_data:
                    table = Table(title="API Metrics")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="green")
                    
                    for metric, value in sorted(metrics_data.items()):
                        table.add_row(metric, value)
                    
                    console.print(table)
                else:
                    console.print("[yellow]No metrics available[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Failed to fetch metrics: {e}[/red]")
        sys.exit(1)

@app.command()
def test_api(
    url: str = typer.Option("http://localhost:8080", "--url", "-u", help="API URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
    prompt: str = typer.Option("Hello, world!", "--prompt", "-p", help="Test prompt"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of test requests")
):
    """Test the inference API with sample requests."""
    import httpx
    token = token or os.getenv("TRUTHGPT_API_TOKEN", "changeme")
    
    console.print(f"[bold]Testing API: {url}[/bold]")
    
    with Progress() as progress:
        task = progress.add_task("Sending requests...", total=iterations)
        
        results = []
        for i in range(iterations):
            try:
                with httpx.Client(timeout=30.0) as client:
                    start = time.time()
                    response = client.post(
                        f"{url}/v1/infer",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "model": "gpt-4o",
                            "prompt": prompt,
                            "params": {
                                "max_new_tokens": 64,
                                "temperature": 0.7
                            }
                        }
                    )
                    elapsed = time.time() - start
                    response.raise_for_status()
                    
                    results.append({
                        "iteration": i + 1,
                        "status": response.status_code,
                        "latency_ms": elapsed * 1000,
                        "success": True
                    })
            except Exception as e:
                results.append({
                    "iteration": i + 1,
                    "status": "error",
                    "error": str(e),
                    "success": False
                })
            
            progress.update(task, advance=1)
    
    # Display results
    table = Table(title="Test Results")
    table.add_column("Iteration", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Latency (ms)", style="yellow")
    
    successful = sum(1 for r in results if r.get("success"))
    avg_latency = sum(r.get("latency_ms", 0) for r in results if r.get("success")) / max(successful, 1)
    
    for result in results:
        status_str = str(result.get("status", "N/A"))
        latency_str = f"{result.get('latency_ms', 0):.2f}" if result.get("success") else "N/A"
        table.add_row(
            str(result["iteration"]),
            "[green]✓[/green] " + status_str if result.get("success") else "[red]✗[/red] " + status_str,
            latency_str
        )
    
    console.print(table)
    console.print(f"\n[bold]Success Rate:[/bold] {successful}/{iterations} ({successful/iterations*100:.1f}%)")
    console.print(f"[bold]Average Latency:[/bold] {avg_latency:.2f}ms")

@app.command()
def version():
    """Show version information."""
    import torch
    try:
        import importlib.metadata
        version = importlib.metadata.version("frontier-model-run")
    except:
        version = "1.0.0"
    
    console.print(Panel(
        f"[bold]Frontier-Model-Run[/bold]\n"
        f"Version: {version}\n"
        f"Python: {sys.version.split()[0]}\n"
        f"PyTorch: {torch.__version__ if torch else 'N/A'}",
        title="📦 Version Info",
        border_style="blue"
    ))

if __name__ == "__main__":
    app()


