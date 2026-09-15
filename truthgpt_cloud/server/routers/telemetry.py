"""
📊 TruthGPT Cloud Server - Telemetry, Observability & Health Router
Exposes Prometheus metrics, system resources, SLA error budgets, circuit breaker resilience, and Kubernetes health probes.
"""

import time
from dataclasses import asdict
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from ..models import RegisterAlertRuleRequest
from ...telemetry.collector import cloud_telemetry
from ...telemetry.prometheus import (
    format_prometheus_metrics,
    generate_prometheus_metrics,
    CONTENT_TYPE_LATEST,
)
from ...telemetry.system_metrics import get_system_metrics
from ...security.manager import cloud_security
from ...routing.router import cloud_router
from ...core.health import cloud_health_checker
from ...core.secrets import cloud_secrets

router = APIRouter(tags=["Telemetry & Observability"])


@router.get("/")
async def root(request: Request):
    """Root platform descriptor; redirects to /dashboard (307 for browser HTML, 302 generic), or returns JSON if requesting application/json."""
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return {
            "platform": "TruthGPT Cloud",
            "version": "2.2.0-cloud",
            "status": "ONLINE",
            "dashboard_url": "/dashboard",
            "admin_url": "/admin",
            "features": [
                "Tiered Subscription Engine (Free, Pro, Ultra, Enterprise)",
                "Executive Monetization & Churn Analytics Dashboard",
                "Z3 SMT Formal Theorem Prover with Merkle Proof Trees",
                "Autonomous Multi-Agent Swarm with Dynamic Consensus",
                "TensorRT-LLM GPU Priority Routing & SSE Streaming",
                "Semantic Proof & KV Cache (<1ms lookup)",
                "Real-time Telemetry & Observability"
            ]
        }
    status_code = 307 if "text/html" in accept else 302
    return RedirectResponse(url="/dashboard", status_code=status_code)


@router.get("/api/v1/health")
async def health():
    """Basic health endpoint."""
    return {"status": "healthy", "service": "truthgpt-cloud-core", "uptime": "nominal"}


@router.get("/api/v1/cloud/health")
async def get_health_endpoint():
    """Operational readiness and diagnostic health of all TruthGPT Cloud services."""
    return cloud_telemetry.get_health_status()


@router.get("/api/v1/telemetry/system")
async def get_system_telemetry():
    """Retrieve real-time hardware telemetry of host node (CPU, RAM, Disk, Process) via psutil."""
    try:
        return {"success": True, "system_metrics": get_system_metrics()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/v1/cloud/telemetry/metrics")
@router.get("/api/v1/cloud/telemetry/stats")
async def get_telemetry_metrics():
    """Retrieve live cluster telemetry, percentiles, and soundness stats."""
    metrics = cloud_telemetry.get_cluster_metrics()
    return {"success": True, "metrics": metrics, "telemetry": metrics}


@router.get("/metrics")
@router.get("/api/v1/cloud/telemetry/prometheus")
async def get_prometheus_metrics_endpoint():
    """Export standard Prometheus line-protocol metrics for scraping."""
    metrics = cloud_telemetry.get_cluster_metrics()
    try:
        raw_payload = generate_prometheus_metrics(metrics)
        return Response(content=raw_payload, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        text = format_prometheus_metrics(metrics)
        return PlainTextResponse(text, media_type="text/plain")


@router.get("/api/v1/cloud/telemetry/alerts")
async def list_alerts_endpoint():
    """List active alert rules and recent alert trigger history."""
    return {
        "success": True,
        "rules": cloud_telemetry.list_alert_rules(),
        "history": cloud_telemetry.get_alert_history()
    }


@router.post("/api/v1/cloud/telemetry/alerts")
async def register_alert_rule_endpoint(req: RegisterAlertRuleRequest):
    """Register a new automated alerting rule."""
    rule = cloud_telemetry.register_alert_rule(
        name=req.name,
        metric_key=req.metric_key,
        threshold=req.threshold,
        comparison=req.comparison or "gte",
        cooldown_seconds=req.cooldown_seconds or 60.0
    )
    return {
        "success": True,
        "rule": {
            "name": rule.name,
            "metric_key": rule.metric_key,
            "threshold": rule.threshold,
            "comparison": rule.comparison,
            "cooldown_seconds": rule.cooldown_seconds
        }
    }


@router.get("/api/v1/cloud/telemetry/error-budget")
async def get_error_budget_endpoint(sla_target: float = Query(99.9, ge=90.0, le=100.0)):
    """Calculate error budget burndown and projected exhaustion for SRE workflows."""
    burndown = cloud_telemetry.get_error_budget_burndown(sla_target=sla_target)
    return {"success": True, "error_budget": burndown}


@router.get("/api/v1/cloud/telemetry/grafana-dashboard")
async def get_grafana_dashboard_endpoint():
    """Export Grafana dashboard JSON configuration for cluster observability."""
    return cloud_telemetry.generate_grafana_dashboard_json()


@router.get("/api/v1/cloud/telemetry/sla")
async def get_sla_metrics_endpoint():
    """Retrieve real-time SLA uptime percentage, error budget, and target compliance."""
    return {"success": True, "sla": cloud_telemetry.get_sla_status()}


# ---------------------------------------------------------------------------
# 🔒 Audit Ledger & Resilience
# ---------------------------------------------------------------------------

@router.get("/api/v1/cloud/audit/ledger")
async def get_audit_ledger_endpoint(limit: int = Query(50, ge=1, le=500)):
    """Retrieve immutable SHA-256 hash-chained cryptographic audit ledger blocks."""
    blocks = cloud_security.get_audit_ledger(limit=limit)
    return {"success": True, "total_blocks": len(blocks), "blocks": blocks}


@router.get("/api/v1/cloud/audit/ledger/verify")
async def verify_audit_ledger_endpoint():
    """Verify cryptographic integrity of the audit ledger from genesis block."""
    return cloud_security.verify_ledger_integrity()


@router.get("/api/v1/cloud/resilience/status")
async def get_resilience_status():
    """Retrieve circuit breaker status and operational metrics."""
    cb_status = cloud_router._circuit_breaker.get_status() if hasattr(cloud_router, "_circuit_breaker") else {"state": "CLOSED"}
    return {"success": True, "circuit_breaker": cb_status}


@router.post("/api/v1/cloud/resilience/reset")
async def reset_circuit_breaker_endpoint():
    """Force reset circuit breaker to CLOSED state."""
    if hasattr(cloud_router, "_circuit_breaker"):
        cloud_router._circuit_breaker.reset()
    return {"success": True, "message": "Circuit breaker reset to CLOSED state"}


# ---------------------------------------------------------------------------
# 🏥 Kubernetes Probes & Diagnostics
# ---------------------------------------------------------------------------

@router.get("/api/v1/cloud/health/liveness")
@router.get("/livez")
async def liveness_probe():
    """Kubernetes liveness probe ensuring process responsiveness."""
    return {"status": "ok", "timestamp": time.time(), "service": "truthgpt_cloud"}


@router.get("/api/v1/cloud/health/readiness")
@router.get("/readyz")
async def readiness_probe():
    """Kubernetes readiness probe validating storage, cache, verifier, and swarm subsystems."""
    readiness = cloud_health_checker.check_readiness()
    return readiness.to_dict() if hasattr(readiness, "to_dict") else asdict(readiness)


@router.get("/api/v1/cloud/health/diagnostics")
async def platform_diagnostics_endpoint():
    """Deep platform diagnostic inspection of hardware, runtime, solvers, and subsystems."""
    return cloud_health_checker.get_platform_diagnostics()


@router.get("/api/v1/cloud/health/secrets-audit")
async def secrets_audit_endpoint():
    """Audit status and presence of essential cloud credentials and encryption secrets."""
    return {
        "success": True,
        "secrets_audit": cloud_secrets.audit_secrets_presence(),
    }


__all__ = ["router"]
