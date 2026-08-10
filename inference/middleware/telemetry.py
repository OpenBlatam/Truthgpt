"""
Telemetry Middleware

Provides ASGI middleware for Prometheus metrics and OpenTelemetry tracing
for the Inference API.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TelemetryState:
    """Global telemetry state holding counters and metrics."""
    metrics: Dict[str, Any] = defaultdict(int)

telemetry_state = TelemetryState()

try:
    from ..monitoring.metrics import metrics_collector
except (ImportError, ValueError):
    metrics_collector = None

class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to record metrics (latency, request count, error count).
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", "unknown")
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            telemetry_state.metrics["errors_5xx"] += 1
            if metrics_collector:
                metrics_collector.increment("inference_errors_5xx_total")
            raise e
            
        latency_ms = (time.time() - start_time) * 1000
        
        telemetry_state.metrics["requests_total"] += 1
        telemetry_state.metrics["request_duration_ms"] += latency_ms
        if metrics_collector:
            metrics_collector.increment("inference_requests_total")
            metrics_collector.observe("inference_request_duration_ms", latency_ms)
            metrics_collector.record_request_time(latency_ms)
        
        if response.status_code >= 500:
            telemetry_state.metrics["errors_5xx"] += 1
            if metrics_collector:
                metrics_collector.increment("inference_errors_5xx_total")
            
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}"
        
        return response

def get_metrics_text() -> str:
    """Format metrics in Prometheus text format."""
    if metrics_collector:
        return metrics_collector.export_prometheus()

    total_requests = telemetry_state.metrics.get("requests_total", 0)
    total_duration = telemetry_state.metrics.get("request_duration_ms", 0)
    avg_duration = total_duration / total_requests if total_requests > 0 else 0
    errors_5xx = telemetry_state.metrics.get("errors_5xx", 0)
    cache_hits = telemetry_state.metrics.get("cache_hits", 0)
    
    lines = [
        "# HELP inference_requests_total Total number of inference requests",
        "# TYPE inference_requests_total counter",
        f"inference_requests_total {total_requests}",
        "",
        "# HELP inference_request_duration_ms Average request duration in milliseconds",
        "# TYPE inference_request_duration_ms gauge",
        f"inference_request_duration_ms {avg_duration:.2f}",
        "",
        "# HELP inference_errors_5xx_total Total number of 5xx errors",
        "# TYPE inference_errors_5xx_total counter",
        f"inference_errors_5xx_total {errors_5xx}",
        "",
        "# HELP inference_cache_hits_total Total number of cache hits",
        "# TYPE inference_cache_hits_total counter",
        f"inference_cache_hits_total {cache_hits}",
        ""
    ]
    return "\n".join(lines)

