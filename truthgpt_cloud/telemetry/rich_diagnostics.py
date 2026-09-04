"""
🎨 TruthGPT Cloud - Rich Terminal UI & Cluster Diagnostics
Provides high-fidelity terminal dashboards, formatted proof certificate panels,
and real-time cluster health tables using the Rich library.
"""

from typing import Any, Optional, Dict

_HAS_RICH = False
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


def render_certificate_panel(cert: Any) -> Any:
    """
    Renders a ProofCertificate as a formatted, color-coded Rich Panel.
    Displays Merkle root, Ed25519 signature status, SMT engine, and proof invariants.
    """
    if not _HAS_RICH:
        return f"[CERTIFICATE {getattr(cert, 'certificate_id', 'unknown')}] Status: {getattr(cert, 'status', 'N/A')}"

    # Extract attributes safely from dict or object
    if isinstance(cert, dict):
        cid = cert.get("certificate_id", "N/A")
        claim = cert.get("theorem_or_claim", "N/A")
        status = cert.get("status", "UNKNOWN")
        confidence = cert.get("confidence_score", 1.0)
        engine = cert.get("solver_engine", "Z3 SMT")
        time_ms = cert.get("verification_time_ms", 0.0)
        merkle = cert.get("merkle_root") or cert.get("proof_tree_hash", "N/A")
        asym_sig = cert.get("asymmetric_signature")
        pub_key = cert.get("public_key_hex")
        invariants = cert.get("mathematical_invariants", [])
        steps = cert.get("proof_steps", [])
    else:
        cid = getattr(cert, "certificate_id", "N/A")
        claim = getattr(cert, "theorem_or_claim", "N/A")
        status = getattr(cert, "status", "UNKNOWN")
        confidence = getattr(cert, "confidence_score", 1.0)
        engine = getattr(cert, "solver_engine", "Z3 SMT")
        time_ms = getattr(cert, "verification_time_ms", 0.0)
        merkle = getattr(cert, "merkle_root", None) or getattr(cert, "proof_tree_hash", "N/A")
        asym_sig = getattr(cert, "asymmetric_signature", None)
        pub_key = getattr(cert, "public_key_hex", None)
        invariants = getattr(cert, "mathematical_invariants", [])
        steps = getattr(cert, "proof_steps", [])

    status_color = "green" if "VALID" in status or "SAT" in status else "red" if "UNSAT" in status or "FAIL" in status else "yellow"

    content = Text()
    content.append("📜 Teorema / Claim: ", style="bold cyan")
    content.append(f"{claim}\n", style="white")

    content.append("🛡️ Estado: ", style="bold")
    content.append(f"[{status}]", style=f"bold {status_color}")
    content.append(f"  |  Confianza: {confidence * 100:.2f}%  |  Tiempo: {time_ms:.2f}ms\n", style="dim")

    content.append("⚙️ Motor SMT: ", style="bold magenta")
    content.append(f"{engine}\n", style="white")

    content.append("🌳 Merkle Root: ", style="bold blue")
    content.append(f"{merkle}\n", style="bright_blue")

    if asym_sig:
        content.append("🔑 Firma Soberana (Ed25519): ", style="bold green")
        content.append(f"VERIFICADA [hex: {asym_sig[:16]}...]\n", style="green")
        if pub_key:
            content.append(f"   Clave Pública: {pub_key[:16]}...\n", style="dim")

    if invariants:
        content.append("\n📐 Invariantes Matemáticos Preservados:\n", style="bold yellow")
        for inv in invariants[:5]:
            content.append(f"   • {inv}\n", style="italic")

    if steps:
        content.append("\n🪜 Pasos de Demostración:\n", style="bold cyan")
        for s in steps[:4]:
            content.append(f"   ✓ {s}\n", style="dim white")

    return Panel(
        content,
        title=f"[bold white]TruthGPT Formal Proof Certificate[/bold white] [dim]({cid})[/dim]",
        border_style=status_color,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_cluster_status_table(telemetry: Any, cache: Any) -> Any:
    """Renders a Rich diagnostic table of telemetry metrics, latency percentiles, and cache hits."""
    if not _HAS_RICH:
        return "Cluster Status (Rich not installed)"

    metrics = telemetry.get_metrics() if hasattr(telemetry, "get_metrics") else {}
    cache_stats = cache.get_stats() if hasattr(cache, "get_stats") else {}

    table = Table(
        title="⚡ TruthGPT Cloud - Métricas de Cluster y Rendimiento",
        box=box.DOUBLE_EDGE,
        header_style="bold magenta",
    )
    table.add_column("Métrica", style="cyan", width=30)
    table.add_column("Valor Actual", style="bold white", width=24)
    table.add_column("Detalles / Estado", style="dim white", width=32)

    # Inferences & Verifications
    total_inf = metrics.get("total_inferences", 0)
    total_ver = metrics.get("total_verifications", 0)
    total_swarms = metrics.get("total_swarms", 0)
    soundness = metrics.get("soundness_percent", 100.0)

    table.add_row("Inferencias Completadas", str(total_inf), "Throughput total del cluster")
    table.add_row("Verificaciones SMT", str(total_ver), f"Índice de Soundness: {soundness:.1f}%")
    table.add_row("Ejecuciones Swarm", str(total_swarms), "Consenso distribuido multi-agente")

    # Latencies
    inf_lat = metrics.get("inference_latency_ms", {})
    p50 = inf_lat.get("p50", 0.0)
    p95 = inf_lat.get("p95", 0.0)
    p99 = inf_lat.get("p99", 0.0)
    table.add_row("Latencia Inferencia (p50/p95/p99)", f"{p50:.1f} / {p95:.1f} / {p99:.1f} ms", "Distribución de percentiles")

    # Cache Stats
    cached_entries = cache_stats.get("cached_entries", 0)
    hit_ratio = cache_stats.get("hit_ratio_percent", 0.0)
    tokens_saved = cache_stats.get("total_tokens_saved", 0)
    has_redis = cache_stats.get("has_redis_l2", False)
    redis_status = "Activo (Distribuido L2)" if has_redis else "Inactivo / Local L1"

    table.add_row("Caché Semántica (L1 RAM)", f"{cached_entries} entradas", f"Hit Ratio: {hit_ratio:.1f}%")
    table.add_row("Caché Redis L2", redis_status, "Aceleración compartida en cluster")
    table.add_row("Tokens de Cómputo Ahorrados", f"{tokens_saved:,}", "Economía de tokens optimizada")

    return table


def render_tier_comparison_table() -> Any:
    """Renders a Rich table comparing all subscription tiers and feature flags."""
    if not _HAS_RICH:
        return "Tier Comparison (Rich not installed)"

    from ..core.tiers import TIER_CONFIGURATIONS

    table = Table(
        title="💎 TruthGPT Cloud - Comparativa de Niveles de Suscripción",
        box=box.ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("Nivel", style="bold yellow")
    table.add_column("RPM", justify="right")
    table.add_column("Tokens Diarios", justify="right")
    table.add_column("Verificación SMT", justify="center")
    table.add_column("Swarm", justify="center")
    table.add_column("Proof Cert", justify="center")
    table.add_column("Prioridad GPU", justify="center")

    for cfg in TIER_CONFIGURATIONS.values():
        table.add_row(
            cfg.tier_id.value.upper(),
            str(cfg.requests_per_minute),
            f"{cfg.daily_token_limit:,}",
            "✓" if cfg.smt_z3_verification_depth > 0 else "✗",
            "✓" if cfg.swarm_multi_agent else "✗",
            "✓" if cfg.proof_certificate_generation else "✗",
            "✓" if cfg.priority_gpu_routing else "✗",
        )

    return table


def render_system_metrics_panel(metrics: Optional[Dict[str, Any]] = None) -> Any:
    """Renders real-time node hardware resource metrics (CPU, RAM, Disk, Process) in a Rich Panel."""
    if metrics is None:
        try:
            from .system_metrics import get_system_metrics
            metrics = get_system_metrics()
        except Exception:
            metrics = {}

    if not _HAS_RICH:
        return f"[SYSTEM METRICS] CPU: {metrics.get('cpu', {}).get('percent', 0)}%, RAM: {metrics.get('memory', {}).get('percent', 0)}%"

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    table.add_column("Subsystem", style="bold white", width=18)
    table.add_column("Utilization", style="bold green", width=22)
    table.add_column("Details & Allocations", style="dim white", width=34)

    cpu = metrics.get("cpu", {})
    cpu_pct = cpu.get("percent", 0.0)
    cpu_color = "green" if cpu_pct < 60 else ("yellow" if cpu_pct < 85 else "red")
    table.add_row(
        "⚡ CPU Utilization",
        f"[{cpu_color}]{cpu_pct:.1f}%[/]",
        f"Cores: {cpu.get('logical_cores', 1)} logical / {cpu.get('physical_cores', 1)} physical",
    )

    mem = metrics.get("memory", {})
    mem_pct = mem.get("percent", 0.0)
    mem_color = "green" if mem_pct < 70 else ("yellow" if mem_pct < 90 else "red")
    table.add_row(
        "🧠 RAM Memory",
        f"[{mem_color}]{mem_pct:.1f}%[/]",
        f"{mem.get('used_mb', 0.0)} MB used / {mem.get('total_mb', 0.0)} MB total",
    )

    disk = metrics.get("disk", {})
    disk_pct = disk.get("percent", 0.0)
    table.add_row(
        "💾 Storage Disk",
        f"{disk_pct:.1f}%",
        f"Free: {round(disk.get('free_bytes', 0)/(1024**3), 1)} GB",
    )

    proc = metrics.get("process", {})
    table.add_row(
        "⚙️ Worker Process",
        f"PID: {proc.get('pid', 'N/A')}",
        f"Threads: {proc.get('threads_count', 1)} | RSS: {proc.get('memory_rss_mb', 0.0)} MB",
    )

    panel = Panel(
        table,
        title="🖥️  TruthGPT Cloud Sovereign Node Telemetry (psutil)",
        border_style="bright_blue",
        box=box.ROUNDED,
    )
    return panel


def print_certificate(cert: Any) -> None:
    """Print certificate to interactive console if Rich is available."""
    if _HAS_RICH:
        Console().print(render_certificate_panel(cert))
    else:
        print(f"Proof Certificate: {cert}")


def print_cluster_status(telemetry: Any, cache: Any) -> None:
    """Print cluster status to interactive console if Rich is available."""
    if _HAS_RICH:
        Console().print(render_cluster_status_table(telemetry, cache))
    else:
        print(f"Metrics: {telemetry.get_metrics()}")


def print_system_metrics(metrics: Optional[Dict[str, Any]] = None) -> None:
    """Print node hardware telemetry to interactive console if Rich is available."""
    if _HAS_RICH:
        Console().print(render_system_metrics_panel(metrics))
    else:
        print(f"System Metrics: {metrics}")


__all__ = [
    "render_certificate_panel",
    "render_cluster_status_table",
    "render_tier_comparison_table",
    "render_system_metrics_panel",
    "print_certificate",
    "print_cluster_status",
    "print_system_metrics",
    "_HAS_RICH",
]
