"""
📊 TruthGPT Cloud - Enterprise Prometheus Metrics Exporter
Provides native prometheus_client metrics registry, counters, gauges, histograms,
and fallback Prometheus exposition line protocol formatter.
"""

from typing import Dict, Any, Optional

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    _HAS_PROMETHEUS_CLIENT = True
except ImportError:
    _HAS_PROMETHEUS_CLIENT = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


if _HAS_PROMETHEUS_CLIENT:
    _REGISTRY = CollectorRegistry(auto_describe=True)

    PROM_INFERENCES_TOTAL = Counter(
        "truthgpt_cloud_inferences_total",
        "Total number of inference queries served",
        registry=_REGISTRY,
    )
    PROM_VERIFICATIONS_TOTAL = Counter(
        "truthgpt_cloud_verifications_total",
        "Total formal theorem verifications executed",
        ["status"],
        registry=_REGISTRY,
    )
    PROM_SWARMS_TOTAL = Counter(
        "truthgpt_cloud_swarms_total",
        "Total multi-agent swarm sessions",
        registry=_REGISTRY,
    )
    PROM_UPTIME_SECONDS = Gauge(
        "truthgpt_cloud_uptime_seconds",
        "Total cloud uptime in seconds",
        registry=_REGISTRY,
    )
    PROM_SOUNDNESS_PERCENT = Gauge(
        "truthgpt_cloud_soundness_percent",
        "Formal mathematical soundness rate",
        registry=_REGISTRY,
    )
    PROM_LATENCY_SECONDS = Histogram(
        "truthgpt_cloud_latency_seconds",
        "Inference latency distribution in seconds",
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=_REGISTRY,
    )
else:
    _REGISTRY = None
    PROM_INFERENCES_TOTAL = None
    PROM_VERIFICATIONS_TOTAL = None
    PROM_SWARMS_TOTAL = None
    PROM_UPTIME_SECONDS = None
    PROM_SOUNDNESS_PERCENT = None
    PROM_LATENCY_SECONDS = None


def get_prometheus_registry() -> Optional[Any]:
    """Retrieve the dedicated TruthGPT Cloud Prometheus CollectorRegistry."""
    return _REGISTRY


def update_prometheus_metrics(metrics: Dict[str, Any]) -> None:
    """Update Prometheus Gauges with latest snapshot from telemetry collector."""
    if not _HAS_PROMETHEUS_CLIENT:
        return
    if PROM_UPTIME_SECONDS is not None:
        PROM_UPTIME_SECONDS.set(float(metrics.get("uptime_seconds", 0.0)))
    if PROM_SOUNDNESS_PERCENT is not None:
        PROM_SOUNDNESS_PERCENT.set(float(metrics.get("formal_soundness_percent", 100.0)))


def generate_prometheus_metrics(metrics: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Generate standard Prometheus metrics payload.
    Uses prometheus_client.generate_latest if available, or formats line protocol string.
    """
    if metrics:
        update_prometheus_metrics(metrics)

    if _HAS_PROMETHEUS_CLIENT and _REGISTRY is not None:
        return generate_latest(_REGISTRY)

    # Fallback to text formatting
    txt = format_prometheus_metrics(metrics or {})
    return txt.encode("utf-8")


def format_prometheus_metrics(metrics: Dict[str, Any]) -> str:
    """Format a metrics dictionary into Prometheus line protocol text (backward-compatible)."""
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


__all__ = [
    "format_prometheus_metrics",
    "generate_prometheus_metrics",
    "update_prometheus_metrics",
    "get_prometheus_registry",
    "CONTENT_TYPE_LATEST",
    "PROM_INFERENCES_TOTAL",
    "PROM_VERIFICATIONS_TOTAL",
    "PROM_SWARMS_TOTAL",
    "PROM_UPTIME_SECONDS",
    "PROM_SOUNDNESS_PERCENT",
    "PROM_LATENCY_SECONDS",
    "_HAS_PROMETHEUS_CLIENT",
]
