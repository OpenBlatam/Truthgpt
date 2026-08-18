"""
Training Visualization and Run Summary Utilities.

Provides functions to visualize checkpoints, summarize training runs,
plot training loss curves, and inspect memory consumption profiles.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def summarize_run(run_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Summarize details of a training run directory.

    Args:
        run_dir: Path to the training run directory.

    Returns:
        Dictionary containing run summary metadata.
    """
    run_path = Path(run_dir)
    summary: Dict[str, Any] = {
        "name": run_path.name,
        "path": str(run_path.resolve()),
        "exists": run_path.exists(),
        "checkpoints": [],
        "total_checkpoint_size_mb": 0.0,
        "config": None,
        "metrics": {},
        "has_best": False,
        "has_last": False,
    }

    if not run_path.exists() or not run_path.is_dir():
        return summary

    # Scan for checkpoints
    for item in sorted(run_path.iterdir()):
        if item.is_file() and item.suffix in [".pt", ".bin", ".safetensors", ".ckpt"]:
            size_mb = item.stat().st_size / (1024 * 1024)
            summary["checkpoints"].append({
                "name": item.name,
                "path": str(item),
                "size_mb": round(size_mb, 2),
                "modified": item.stat().st_mtime,
            })
            summary["total_checkpoint_size_mb"] += size_mb
            if "best" in item.stem.lower():
                summary["has_best"] = True
            if "last" in item.stem.lower() or "final" in item.stem.lower():
                summary["has_last"] = True

        elif item.is_dir() and ((item / "config.json").exists() or (item / "pytorch_model.bin").exists() or (item / "model.safetensors").exists()):
            # HuggingFace style checkpoint folder
            size_mb = sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) / (1024 * 1024)
            summary["checkpoints"].append({
                "name": item.name,
                "path": str(item),
                "size_mb": round(size_mb, 2),
                "is_dir": True,
            })
            summary["total_checkpoint_size_mb"] += size_mb
            if "best" in item.name.lower():
                summary["has_best"] = True
            if "last" in item.name.lower() or "final" in item.name.lower():
                summary["has_last"] = True

    summary["total_checkpoint_size_mb"] = round(summary["total_checkpoint_size_mb"], 2)

    # Scan for config files
    config_file = run_path / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                summary["config"] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read config.json in {run_path}: {e}")

    # Scan for metrics files
    metrics_file = run_path / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                summary["metrics"] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read metrics.json in {run_path}: {e}")

    return summary


def visualize_checkpoints(
    run_dir: Union[str, Path],
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inspect and format a visual breakdown of checkpoints in a training run.

    Args:
        run_dir: Path to the training run directory.
        save_path: Optional path to save text/json summary report.

    Returns:
        Summary dict containing formatted checkpoint details.
    """
    summary = summarize_run(run_dir)
    checkpoints = summary["checkpoints"]

    header = f"=== Checkpoints for Run: {summary['name']} ==="
    lines = [
        header,
        f"Directory: {summary['path']}",
        f"Total Checkpoints: {len(checkpoints)}",
        f"Total Storage: {summary['total_checkpoint_size_mb']} MB",
        "-" * len(header),
    ]

    if not checkpoints:
        lines.append("  (No checkpoints found)")
    else:
        for idx, ckpt in enumerate(checkpoints, 1):
            tag = ""
            if "best" in ckpt["name"].lower():
                tag = " [BEST]"
            elif "last" in ckpt["name"].lower() or "final" in ckpt["name"].lower():
                tag = " [LATEST]"
            lines.append(f"  {idx:2d}. {ckpt['name']:<30} {ckpt['size_mb']:>8.2f} MB{tag}")

    report_text = "\n".join(lines)
    summary["report_text"] = report_text

    if save_path:
        out = Path(save_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".json":
            with open(out, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        else:
            with open(out, "w", encoding="utf-8") as f:
                f.write(report_text)

    return summary


def plot_loss_curves(
    loss_history: List[float],
    val_loss_history: Optional[List[float]] = None,
    output_path: Optional[str] = None,
    title: str = "Training & Validation Loss",
) -> Optional[str]:
    """
    Generate loss curves plot if matplotlib is available, or ASCII table fallback.

    Args:
        loss_history: List of training loss values.
        val_loss_history: Optional list of validation loss values.
        output_path: Optional file path to save the generated image.
        title: Plot title.

    Returns:
        Output file path if plotted to disk, or None.
    """
    if not loss_history:
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(loss_history, label="Training Loss", color="#2563EB", linewidth=2.0)
        if val_loss_history:
            ax.plot(val_loss_history, label="Validation Loss", color="#DC2626", linewidth=2.0, linestyle="--")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Epoch / Step")
        ax.set_ylabel("Loss")
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150)
            plt.close(fig)
            return output_path
        plt.close(fig)
        return None
    except ImportError:
        logger.info("matplotlib not installed; skipping graphical loss plot generation.")
        return None


def visualize_memory_profile(
    profile_data: Dict[str, Any],
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Format and visualize memory usage profile metrics.

    Args:
        profile_data: Dictionary with memory statistics.
        output_path: Optional path to save text report.

    Returns:
        Structured memory summary dictionary.
    """
    summary = {
        "peak_gpu_memory_mb": profile_data.get("peak_gpu_memory_mb", 0.0),
        "allocated_gpu_memory_mb": profile_data.get("allocated_gpu_memory_mb", 0.0),
        "reserved_gpu_memory_mb": profile_data.get("reserved_gpu_memory_mb", 0.0),
        "system_ram_used_gb": profile_data.get("system_ram_used_gb", 0.0),
    }

    report = (
        "=== Memory Usage Profile ===\n"
        f"Peak GPU Allocated : {summary['peak_gpu_memory_mb']:.2f} MB\n"
        f"Current GPU Alloc  : {summary['allocated_gpu_memory_mb']:.2f} MB\n"
        f"GPU Reserved       : {summary['reserved_gpu_memory_mb']:.2f} MB\n"
        f"System RAM Used    : {summary['system_ram_used_gb']:.2f} GB\n"
    )
    summary["report_text"] = report

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(report)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Training Visualization Tools")
    parser.add_argument("--run-dir", type=str, default="runs", help="Training run directory")
    parser.add_argument("--save-report", type=str, default=None, help="Save report to file")
    args = parser.parse_args()

    res = visualize_checkpoints(args.run_dir, save_path=args.save_report)
    print(res["report_text"])


if __name__ == "__main__":
    main()
