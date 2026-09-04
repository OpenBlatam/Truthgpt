"""
📊 TruthGPT Cloud - Telemetry & Observability Subpackage
Exports real-time metrics collection, audit logging, and Prometheus formatters.
"""

from .prometheus import (
    format_prometheus_metrics,
    generate_prometheus_metrics,
    get_prometheus_registry,
    update_prometheus_metrics,
    CONTENT_TYPE_LATEST,
)
from .collector import (
    AuditLogEntry,
    AlertRule,
    CloudTelemetryCollector,
    cloud_telemetry,
)
from .structured_logging import (
    get_logger,
    get_cloud_logger,
    configure_logging,
    configure_structured_logging,
    bind_context,
    unbind_context,
    _HAS_STRUCTLOG,
)
from .rich_diagnostics import (
    render_certificate_panel,
    render_cluster_status_table,
    render_tier_comparison_table,
    render_system_metrics_panel,
    print_certificate,
    print_cluster_status,
    print_system_metrics,
    _HAS_RICH,
)
from .system_metrics import (
    get_system_metrics,
    _HAS_PSUTIL,
    PROM_NODE_CPU_PERCENT,
    PROM_NODE_MEMORY_BYTES,
    PROM_NODE_MEMORY_PERCENT,
    PROM_PROCESS_THREADS,
)

__all__ = [
    "AuditLogEntry",
    "AlertRule",
    "CloudTelemetryCollector",
    "cloud_telemetry",
    "format_prometheus_metrics",
    "generate_prometheus_metrics",
    "get_prometheus_registry",
    "update_prometheus_metrics",
    "CONTENT_TYPE_LATEST",
    "get_logger",
    "get_cloud_logger",
    "configure_logging",
    "configure_structured_logging",
    "bind_context",
    "unbind_context",
    "_HAS_STRUCTLOG",
    "render_certificate_panel",
    "render_cluster_status_table",
    "render_tier_comparison_table",
    "render_system_metrics_panel",
    "print_certificate",
    "print_cluster_status",
    "print_system_metrics",
    "_HAS_RICH",
    "get_system_metrics",
    "_HAS_PSUTIL",
    "PROM_NODE_CPU_PERCENT",
    "PROM_NODE_MEMORY_BYTES",
    "PROM_NODE_MEMORY_PERCENT",
    "PROM_PROCESS_THREADS",
]
