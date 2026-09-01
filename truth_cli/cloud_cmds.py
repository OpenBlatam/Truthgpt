"""
💎 TruthGPT Cloud CLI Subcommands
Provides terminal commands for cloud subscriptions, formal verification, and SaaS management.
"""

import sys
import os
import asyncio
from typing import Optional
import typer
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from .core import _fix_param, console


def register_cloud_commands(cloud_app: typer.Typer):

    @cloud_app.command("tiers")
    def list_tiers():
        """List all TruthGPT Cloud subscription tiers and pricing."""
        from truthgpt_cloud import get_all_tiers
        tiers = get_all_tiers()
        
        table = Table(title="💎 TruthGPT Cloud - Planes de Suscripción")
        table.add_column("Tier ID", style="bold cyan")
        table.add_column("Nombre / Badge", style="green")
        table.add_column("Precio Mes / Año", style="yellow")
        table.add_column("Tokens Diarios", style="magenta")
        table.add_column("Verificación SMT", style="blue")
        table.add_column("Latencia", style="white")

        for t in tiers:
            price_str = f"${t['price_monthly_usd']}/mo (${t['price_yearly_usd']}/yr)" if t['price_monthly_usd'] > 0 else "Gratis"
            table.add_row(
                t['tier_id'],
                f"{t['name']} [{t['badge']}]",
                price_str,
                f"{t['daily_token_limit']:,}",
                t['smt_verification_level'],
                t['latency_tier']
            )
        console.print(table)

    @cloud_app.command("status")
    def subscription_status(user_id: str = typer.Option("usr_default_demo", "--user", "-u", help="User ID")):
        """Check active subscription, remaining tokens and quota."""
        from truthgpt_cloud import subscription_manager
        user_id = _fix_param(user_id, "usr_default_demo")
        summary = subscription_manager.get_user_status_summary(user_id)
        
        m = summary["metrics"]
        info = (
            f"[bold cyan]Usuario:[/bold cyan] {summary['name']} ({summary['email']})\n"
            f"[bold green]Nivel:[/bold green] {summary['tier_name']} [{summary['tier_badge']}] (Estado: {summary['status']})\n"
            f"[bold yellow]Tokens Hoy:[/bold yellow] {m['tokens_consumed_today']:,} / {m['daily_token_limit']:,} ({m['percent_quota_used']}% consumido)\n"
            f"[bold magenta]Tokens Restantes:[/bold magenta] {m['remaining_tokens']:,}\n"
            f"[bold blue]Verificaciones SMT Completadas:[/bold blue] {m['verifications_completed']}\n"
            f"[bold white]Ejecuciones Swarm:[/bold white] {m['swarm_runs']}\n"
            f"[bold cyan]Claves API Registradas:[/bold cyan] {len(summary['api_keys'])}"
        )
        console.print(Panel(info, title="📊 Estado de Suscripción TruthGPT Cloud", border_style="cyan"))

    @cloud_app.command("upgrade")
    def upgrade_tier(
        tier: str = typer.Argument(..., help="Nivel objetivo (pro, ultra, enterprise)"),
        user_id: str = typer.Option("usr_default_demo", "--user", "-u", help="User ID"),
        cycle: str = typer.Option("monthly", "--cycle", "-c", help="monthly o yearly")
    ):
        """Upgrade active subscription tier."""
        from truthgpt_cloud import subscription_manager, CloudTier
        try:
            target = CloudTier(tier.lower())
        except ValueError:
            console.print(f"[bold red]❌ Error:[/bold red] Nivel '{tier}' no es válido. Opciones: pro, ultra, enterprise.")
            return

        try:
            res = subscription_manager.upgrade_subscription(
                user_id=user_id,
                target_tier=target,
                billing_cycle=cycle
            )
            console.print(Panel(
                f"✅ [bold green]¡Suscripción actualizada con éxito a {res['tier_name']}![/bold green]\n"
                f"Factura generada: [yellow]{res['invoice']['invoice_id']}[/yellow] por [bold]${res['invoice']['amount_usd']} USD[/bold]\n"
                f"Nuevo límite diario: [magenta]{res['limits']['daily_token_limit']:,} tokens[/magenta]\n"
                f"Nivel de Verificación: [blue]{res['limits']['verification_level']}[/blue]\n"
                f"Cola de Latencia: [white]{res['limits']['latency_tier']}[/white]",
                title="💳 Upgrade Confirmado",
                border_style="green"
            ))
        except Exception as e:
            console.print(f"[bold red]❌ Error al actualizar:[/bold red] {e}")

    @cloud_app.command("verify")
    def verify_expression(
        claim: str = typer.Argument(..., help="Afirmación o fórmula matemática a verificar formalmente"),
        depth: int = typer.Option(2, "--depth", "-d", help="Profundidad de verificación SMT (1: SymPy, 2: Z3, 3: Quantum)")
    ):
        """Verify mathematical invariants and theorems using Cloud SMT Solver."""
        from truthgpt_cloud import cloud_verifier
        console.print(f"[yellow]⏳ Verificando con Solucionador Formal SMT (Nivel {depth})...[/yellow]")
        cert = cloud_verifier.verify_expression(claim_text=claim, tier_depth=depth)
        
        status_color = "green" if cert.status == "PROVED_FORMALLY" else "yellow"
        output = (
            f"[bold {status_color}]Estado: {cert.status}[/bold {status_color}]\n"
            f"[cyan]Certificado ID:[/cyan] {cert.certificate_id}\n"
            f"[blue]Motor SMT:[/blue] {cert.solver_engine}\n"
            f"[magenta]Hash Criptográfico de Prueba:[/magenta] {cert.proof_tree_hash}\n"
            f"[yellow]Tiempo de Verificación:[/yellow] {cert.verification_time_ms} ms\n"
            f"[white]Puntaje de Certeza Formal:[/white] {cert.confidence_score * 100}%\n"
        )
        if cert.mathematical_invariants:
            output += "\n[bold]Invariantes Validados:[/bold]\n"
            for inv in cert.mathematical_invariants:
                output += f" • {inv}\n"

        console.print(Panel(output, title="📜 Certificado de Prueba Formal TruthGPT", border_style=status_color))

    @cloud_app.command("ask")
    def ask_cloud(
        prompt: str = typer.Argument(..., help="Pregunta o consulta para TruthGPT Cloud"),
        model: Optional[str] = typer.Option(None, "--model", "-m", help="Modelo objetivo"),
        swarm: bool = typer.Option(False, "--swarm", "-s", help="Activar Swarm de agentes"),
        verify: bool = typer.Option(True, "--verify", "-v", help="Activar verificación Z3 SMT")
    ):
        """Send prompt to TruthGPT Cloud with tiered routing and formal verification."""
        from truthgpt_cloud import TruthGPTCloudClient
        client = TruthGPTCloudClient()
        console.print("[yellow]⏳ Enrutando petición a través del clúster TruthGPT Cloud...[/yellow]")
        
        async def _run():
            return await client.ask_async(
                prompt=prompt,
                model_override=model,
                enable_swarm=swarm,
                enable_formal_verification=verify
            )
            
        res = asyncio.run(_run())
        console.print(Panel(Markdown(res.content), title=f"🤖 Respuesta ({res.model_name})", border_style="cyan"))
        
        if res.proof_certificate:
            console.print(f"[bold green]📜 Certificado de Verdad:[/bold green] {res.proof_certificate['proof_tree_hash']} ({res.proof_certificate['verification_time_ms']} ms)")
        console.print(f"[dim]⏱️ {res.execution_time_ms} ms | Tokens: {res.tokens_consumed} | Tier: {res.tier_used}[/dim]")

    @cloud_app.command("metrics")
    def cluster_metrics():
        """View real-time TruthGPT Cloud cluster telemetry, latency and soundness."""
        from truthgpt_cloud import cloud_telemetry
        m = cloud_telemetry.get_cluster_metrics()
        
        info = (
            f"[bold cyan]Uptime Clúster:[/bold cyan] {m['uptime_seconds']}s\n"
            f"[bold green]Certeza Formal (Soundness):[/bold green] {m['formal_soundness_percent']}%\n"
            f"[bold yellow]Total Inferencias:[/bold yellow] {m['total_inferences']:,}\n"
            f"[bold blue]Total Verificaciones SMT:[/bold blue] {m['total_verifications']:,}\n"
            f"[bold magenta]Total Swarms Ejecutados:[/bold magenta] {m['total_swarms']:,}\n"
            f"[bold white]Latencia Inferencia (p50 / p95 / p99):[/bold white] {m['inference_latency_ms']['p50']}ms / {m['inference_latency_ms']['p95']}ms / {m['inference_latency_ms']['p99']}ms\n"
            f"[bold white]Latencia SMT Solver (p50 / p95 / p99):[/bold white] {m['smt_solver_latency_ms']['p50']}ms / {m['smt_solver_latency_ms']['p95']}ms / {m['smt_solver_latency_ms']['p99']}ms"
        )
        console.print(Panel(info, title="📊 Telemetría y Rendimiento TruthGPT Cloud", border_style="cyan"))

    @cloud_app.command("verify-attention")
    def verify_attention(
        num_heads_q: int = typer.Option(32, "--heads-q", "-q", help="Cabezas de consulta (Query)"),
        num_heads_kv: int = typer.Option(8, "--heads-kv", "-k", help="Cabezas de valor/clave (KV) para GQA"),
        head_dim: int = typer.Option(128, "--head-dim", "-d", help="Dimensión por cabeza"),
        arch: str = typer.Option("FlashAttention-3", "--arch", "-a", help="Arquitectura de atención")
    ):
        """Formally verify Transformer attention invariants (MHA, GQA, FlashAttention)."""
        from truthgpt_cloud import cloud_verifier
        console.print(f"[yellow]⏳ Verificando invariantes de atención para {arch}...[/yellow]")
        res = cloud_verifier.verify_attention_invariants(
            query_shape=[1, 2048, num_heads_q * head_dim],
            key_shape=[1, 2048, num_heads_kv * head_dim],
            value_shape=[1, 2048, num_heads_kv * head_dim],
            num_heads_q=num_heads_q,
            num_heads_kv=num_heads_kv,
            head_dim=head_dim,
            architecture_type=arch
        )
        color = "green" if res["is_valid"] else "red"
        output = (
            f"[bold {color}]Estado: {'VALIDADO / INVARIANTE PRESERVADO' if res['is_valid'] else 'VIOLACIÓN DETECTADA'}[/bold {color}]\n"
            f"[cyan]Arquitectura:[/cyan] {res['architecture_type']}\n"
            f"[blue]GQA Config:[/blue] Query Heads={num_heads_q}, KV Heads={num_heads_kv} (Ratio {num_heads_q // num_heads_kv}:1)\n"
            f"[magenta]Merkle Proof Root:[/magenta] {res['merkle_root']}\n\n"
            f"[bold]Invariantes Demostrados:[/bold]\n"
        )
        for inv in res["invariants_verified"]:
            output += f" • {inv}\n"

        console.print(Panel(output, title="🛡️ Verificación Formal de Atención Transformer", border_style=color))

    @cloud_app.command("verify-quantization")
    def verify_quant(
        min_val: float = typer.Option(-12.5, "--min", help="Valor mínimo observado"),
        max_val: float = typer.Option(12.5, "--max", help="Valor máximo observado"),
        fmt: str = typer.Option("INT8", "--format", "-f", help="Formato (FP8_E4M3, INT8, INT4, BITNET)")
    ):
        """Formally verify quantization dynamic range and zero-point safety."""
        from truthgpt_cloud import cloud_verifier
        console.print(f"[yellow]⏳ Verificando seguridad de cuantización ({fmt})...[/yellow]")
        res = cloud_verifier.verify_quantization_safety(
            min_val=min_val,
            max_val=max_val,
            quant_format=fmt
        )
        color = "green" if res["is_valid"] else "red"
        output = (
            f"[bold {color}]Estado: {'RANGO DINÁMICO SEGURO' if res['is_valid'] else 'DESBORDAMIENTO'}[/bold {color}]\n"
            f"[cyan]Formato Cuantización:[/cyan] {res['quant_format']} ({res['bits']} bits)\n"
            f"[yellow]Factor de Escala (Delta):[/yellow] {res['scale_factor']:.8f}\n"
            f"[blue]Zero-Point Integer:[/blue] {res['zero_point']} (Rango [{res['q_min']}, {res['q_max']}])\n"
            f"[magenta]Merkle Proof Root:[/magenta] {res['merkle_root']}\n"
        )
        console.print(Panel(output, title="⚡ Verificación de Cuantización", border_style=color))

    @cloud_app.command("audit-ledger")
    def inspect_ledger(limit: int = typer.Option(10, "--limit", "-l", help="Cantidad de bloques")):
        """Inspect the tamper-evident cryptographic SHA-256 audit ledger."""
        from truthgpt_cloud import cloud_security
        integrity = cloud_security.verify_ledger_integrity()
        blocks = cloud_security.get_audit_ledger(limit=limit)

        table = Table(title=f"🔒 Ledger Criptográfico de Auditoría (Integridad: {'✅ OK' if integrity['is_valid'] else '❌ CORRUPTO'})")
        table.add_column("Bloque", style="cyan")
        table.add_column("Evento", style="bold yellow")
        table.add_column("Usuario", style="magenta")
        table.add_column("Hash del Bloque (SHA-256)", style="green")
        table.add_column("Prev Hash", style="dim white")

        for b in blocks:
            table.add_row(
                f"#{b['block_index']}",
                b["event_type"],
                b["user_id"],
                b["block_hash"][:18] + "...",
                b["prev_hash"][:14] + "..."
            )
        console.print(table)

    @cloud_app.command("swarm-debate")
    def run_debate(
        topic: str = typer.Argument(..., help="Tema del debate formal"),
        claim: str = typer.Argument(..., help="Proposición inicial del Blue Team"),
        rounds: int = typer.Option(2, "--rounds", "-r", help="Rondas de refutación")
    ):
        """Execute a Red Team vs Blue Team adversarial debate on TruthGPT Cloud."""
        from truthgpt_cloud import TruthGPTCloudClient
        client = TruthGPTCloudClient()
        console.print(f"[yellow]⏳ Iniciando Debate Adversarial Red Team vs Blue Team: '{topic}'...[/yellow]")
        res = client.execute_adversarial_debate(topic=topic, proponent_claim=claim, rounds=rounds)
        
        output = (
            f"[bold green]Veredicto Final:[/bold green] {res['consensus_verdict']}\n"
            f"[cyan]Acuerdo Inter-Agente:[/cyan] {res['inter_agent_agreement'] * 100:.2f}%\n"
            f"[blue]Probabilidad Bayesiana de Consenso:[/blue] {res['bayesian_consensus_probability'] * 100:.2f}%\n"
            f"[magenta]Rondas Ejecutadas:[/magenta] {res['rounds_count']}\n"
        )
        console.print(Panel(output, title="🐝 Debate Adversarial Swarm Completado", border_style="green"))

    @cloud_app.command("server")
    def run_server(
        port: int = typer.Option(8080, "--port", "-p", help="Puerto HTTP"),
        host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host IP")
    ):
        """Start the TruthGPT Cloud FastAPI server."""
        from truthgpt_cloud_server import start_server
        console.print(Panel(f"Iniciando TruthGPT Cloud Server en http://{host}:{port}", title="🚀 TruthGPT Cloud Server", border_style="green"))
        start_server(host=host, port=port)


