import time
import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
# Heavy imports moved inside commands for speed
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .core import _fix_param, console

def register_model_commands(app: typer.Typer):
    
    @app.command()
    def infer(
        config: str = typer.Option("modules/base/config_management/configs/llm_default.yaml", "--config", "-c", help="Configuration file"),
        text: str = typer.Argument(..., help="Input text for inference"),
        max_new_tokens: int = typer.Option(64, "--max-tokens", "-m", help="Maximum tokens to generate"),
        temperature: float = typer.Option(0.8, "--temperature", "-t", help="Sampling temperature"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (optional)"),
        override: Optional[List[str]] = typer.Option(None, "--override", "-O", help="Config overrides"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
    ):
        """Run inference on text input."""
        config = _fix_param(config, "modules/base/config_management/configs/llm_default.yaml")
        text = _fix_param(text, "")
        max_new_tokens = int(_fix_param(max_new_tokens, 64))
        temperature = float(_fix_param(temperature, 0.8))
        output = _fix_param(output, None)
        override = _fix_param(override, None)
        verbose = bool(_fix_param(verbose, False))
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Loading model...", total=None)
            try:
                from optimization_core.modules.base.config_management.configs.loader import load_config
                cfg = load_config(config, override)
                progress.update(task, description="Building model...")
                from optimization_core.modules.models import create_model
                model = create_model("hf_transformers", cfg.dict())
                progress.update(task, description="Running inference...")
                
                start_time = time.time()
                out = model.infer({
                    "text": text,
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
    def train(
        config: str = typer.Option("modules/base/config_management/configs/llm_default.yaml", "--config", "-c", help="Configuration file"),
        override: Optional[List[str]] = typer.Option(None, "--override", "-O", help="Config overrides")
    ):
        """Train using the existing GenericTrainer and YAML config."""
        config = _fix_param(config, "modules/base/config_management/configs/llm_default.yaml")
        override = _fix_param(override, None)
        
        from optimization_core.scripts.legacy.train_llm import to_cfg as to_trainer_cfg
        from optimization_core.scripts.legacy.train_llm import read_yaml as read_yaml_dict
        from optimization_core.scripts.legacy.train_llm import load_text_splits
        cfg_dict = read_yaml_dict(config)
        merged = {**cfg_dict}
        for ov in (override or []):
            from optimization_core.modules.base.config_management.configs.loader import parse_overrides as _po, deep_merge as _dm
            merged = _dm(merged, _po([ov]))
        trainer_cfg = to_trainer_cfg(merged)

        data_cfg = merged.get("data", {})
        dataset = str(data_cfg.get("dataset", "wikitext"))
        subset = str(data_cfg.get("subset", "wikitext-2-raw-v1"))
        text_field = str(data_cfg.get("text_field", "text"))
        max_seq_len = int(data_cfg.get("max_seq_len", 512))
        limit = int(data_cfg.get("limit", 5000))

        from optimization_core.trainers.trainer import GenericTrainer
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
    def export(
        checkpoint_dir: str = typer.Argument(..., help="Checkpoint directory"),
        onnx_path: str = typer.Option("model.onnx", "--output", "-o", help="Output ONNX path")
    ):
        """Export a HF checkpoint directory to ONNX for fast inference."""
        import torch
        checkpoint_dir = _fix_param(checkpoint_dir, "")
        onnx_path = _fix_param(onnx_path, "model.onnx")
        
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
