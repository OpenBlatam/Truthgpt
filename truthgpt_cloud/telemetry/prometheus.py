"""
📊 TruthGPT Cloud - Prometheus Metrics Exporter
Converts telemetry metrics dictionary to standard Prometheus line protocol.
"""

from typing import Dict, Any


def format_prometheus_metrics(metrics: Dict[str, Any]) -> str:
    """Format a metrics dictionary into Prometheus line protocol text."""
    lines = [
        "# HELP truthgpt_cloud_uptime_seconds Total cloud uptime in seconds",
        "# TYPE truthgpt_cloud_uptime_seconds gauge",
        f"truthgpt_cloud_uptime_seconds {metrics.get('uptime_seconds', 0.0)}",
        "# HELP truthgpt_cloud_inferences_total Total number of inference queries served",
        "# TYPE truthgpt_cloud_inferences_total counter",
        f"truthgpt_cloud_inferences_total {metrics.get('total_inferences', 0)}",
        "# HELP truthgpt_cloud_verifications_total Total formal theorem verifications executed",
        "# TYPE truthgpt_cloud_verifications_total counter",
        f"truthgpt_cloud_verifications_total {metrics.get('total_verifications', 0)}",
        "# HELP truthgpt_cloud_swarms_total Total multi-agent swarm sessions",
        "# TYPE truthgpt_cloud_swarms_total counter",
        f"truthgpt_cloud_swarms_total {metrics.get('total_swarms', 0)}",
        "# HELP truthgpt_cloud_soundness_percent Formal mathematical soundness rate",
        "# TYPE truthgpt_cloud_soundness_percent gauge",
        f"truthgpt_cloud_soundness_percent {metrics.get('formal_soundness_percent', 100.0)}",
        "# HELP truthgpt_cloud_latency_p95_ms 95th percentile inference latency in ms",
        "# TYPE truthgpt_cloud_latency_p95_ms gauge",
        f"truthgpt_cloud_latency_p95_ms {metrics.get('inference_latency_ms', {}).get('p95', 0.0)}",
        "# HELP truthgpt_cloud_smt_latency_p95_ms 95th percentile Z3 SMT solver latency in ms",
        "# TYPE truthgpt_cloud_smt_latency_p95_ms gauge",
        f"truthgpt_cloud_smt_latency_p95_ms {metrics.get('smt_solver_latency_ms', {}).get('p95', 0.0)}",
    ]

    for status, count in metrics.get("proof_status_distribution", {}).items():
        lines.append(f'truthgpt_cloud_proof_status_total{{status="{status}"}} {count}')

    return "\n".join(lines) + "\n"


__all__ = ["format_prometheus_metrics"]
