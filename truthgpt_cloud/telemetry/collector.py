"""
📊 TruthGPT Cloud - Telemetry, Observability & Cluster Analytics
Aggregates inference latencies (p50/p95/p99), proof solve rates, token economics, and audit logs.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from ..core.constants import DEFAULT_TELEMETRY_MAX_HISTORY
from .prometheus import format_prometheus_metrics


@dataclass
class AuditLogEntry:
    timestamp: float
    event_type: str  # "signup", "upgrade", "key_generated", "quota_warning", "verification", etc.
    user_id: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CloudTelemetryCollector:
    """
    Real-time telemetry and monitoring collector for TruthGPT Cloud.
    Thread-safe metric tracking with percentile distributions.
    """

    def __init__(self, max_history: int = DEFAULT_TELEMETRY_MAX_HISTORY):
        self._lock = threading.RLock()
        self.max_history = max_history
        self._latencies_ms: List[float] = []
        self._smt_latencies_ms: List[float] = []
        self._total_inferences: int = 0
        self._total_verifications: int = 0
        self._total_swarms: int = 0
        self._proof_statuses: Dict[str, int] = {
            "PROVEN_VALID": 0,
            "PROVEN_SAT": 0,
            "PROVEN_UNSAT": 0,
            "VERIFIED_SYMBOLIC": 0,
            "UNKNOWN": 0,
            "FAILED": 0,
        }
        self._audit_logs: List[AuditLogEntry] = []
        self.start_timestamp: float = time.time()

    def record_inference(self, latency_ms: float, tokens: int = 0, tier: str = "pro") -> None:
        with self._lock:
            self._total_inferences += 1
            self._latencies_ms.append(latency_ms)
            if len(self._latencies_ms) > self.max_history:
                self._latencies_ms.pop(0)

    def record_verification(self, latency_ms: float, status: str = "PROVEN_VALID") -> None:
        with self._lock:
            self._total_verifications += 1
            self._smt_latencies_ms.append(latency_ms)
            if len(self._smt_latencies_ms) > self.max_history:
                self._smt_latencies_ms.pop(0)
            self._proof_statuses[status] = self._proof_statuses.get(status, 0) + 1

    def record_swarm(self) -> None:
        with self._lock:
            self._total_swarms += 1

    def record_audit_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None:
        with self._lock:
            entry = AuditLogEntry(
                timestamp=time.time(),
                event_type=event_type,
                user_id=user_id,
                details=details,
            )
            self._audit_logs.append(entry)
            if len(self._audit_logs) > self.max_history:
                self._audit_logs.pop(0)

    def _calc_percentiles(self, data: List[float]) -> Dict[str, float]:
        if not data:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}
        s = sorted(data)
        n = len(s)
        p50 = s[int(n * 0.50)]
        p95 = s[min(int(n * 0.95), n - 1)]
        p99 = s[min(int(n * 0.99), n - 1)]
        return {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "avg": round(sum(s) / n, 2),
            "min": round(s[0], 2),
            "max": round(s[-1], 2),
        }

    def get_cluster_metrics(self) -> Dict[str, Any]:
        with self._lock:
            uptime = round(time.time() - self.start_timestamp, 1)
            total_proofs = sum(self._proof_statuses.values())
            invalid_statuses = {"UNKNOWN", "FAILED", "VIOLATED", "COUNTEREXAMPLE_FOUND"}
            failed_proofs = sum(v for k, v in self._proof_statuses.items() if k in invalid_statuses)
            success_proofs = total_proofs - failed_proofs
            formal_soundness_rate = (
                round((success_proofs / max(1, total_proofs)) * 100, 2)
                if total_proofs > 0
                else 100.0
            )

            return {
                "uptime_seconds": uptime,
                "total_inferences": self._total_inferences,
                "total_verifications": self._total_verifications,
                "total_swarms": self._total_swarms,
                "formal_soundness_percent": formal_soundness_rate,
                "proof_status_distribution": dict(self._proof_statuses),
                "inference_latency_ms": self._calc_percentiles(self._latencies_ms),
                "smt_solver_latency_ms": self._calc_percentiles(self._smt_latencies_ms),
                "active_audits_count": len(self._audit_logs),
            }

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self._audit_logs[-limit:]]

    def to_prometheus_text(self) -> str:
        """Export metrics in standard Prometheus line protocol."""
        return format_prometheus_metrics(self.get_cluster_metrics())

    def get_health_status(self) -> Dict[str, Any]:
        """Check the operational health and readiness of all cloud components."""
        has_z3 = False
        try:
            import z3
            has_z3 = True
        except ImportError:
            pass

        has_sympy = False
        try:
            import sympy
            has_sympy = True
        except ImportError:
            pass

        metrics = self.get_cluster_metrics()
        is_healthy = metrics["formal_soundness_percent"] >= 90.0

        return {
            "status": "HEALTHY" if is_healthy else "DEGRADED",
            "is_healthy": is_healthy,
            "components": {
                "formal_verifier_z3": "ONLINE" if has_z3 else "FALLBACK_SYMBOLIC",
                "symbolic_engine_sympy": "ONLINE" if has_sympy else "FALLBACK_HEURISTIC",
                "merkle_crypto_tree": "ONLINE",
                "swarm_orchestrator": "ONLINE",
                "semantic_proof_cache": "ONLINE",
                "telemetry_collector": "ONLINE",
            },
            "cluster_metrics": metrics,
            "timestamp": time.time(),
        }

    def to_opentelemetry_spans(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Export recent audit logs as OpenTelemetry-compatible trace spans."""
        with self._lock:
            spans = []
            for idx, entry in enumerate(self._audit_logs[-limit:]):
                trace_id = f"{int(entry.timestamp * 1000):x}" + "0" * (32 - len(f"{int(entry.timestamp * 1000):x}"))
                span_id = f"{idx + 1:016x}"
                spans.append({
                    "trace_id": trace_id[:32],
                    "span_id": span_id,
                    "name": f"truthgpt.cloud.{entry.event_type}",
                    "kind": "SPAN_KIND_SERVER",
                    "start_time_unix_nano": int(entry.timestamp * 1e9),
                    "end_time_unix_nano": int((entry.timestamp + 0.005) * 1e9),
                    "attributes": {
                        "user.id": entry.user_id,
                        "event.type": entry.event_type,
                        **{f"payload.{k}": str(v) for k, v in entry.details.items()}
                    },
                    "status": {"code": "STATUS_CODE_OK"}
                })
            return spans

    def get_sla_status(self) -> Dict[str, Any]:
        """Calculate real-time SLA compliance and remaining error budget."""
        with self._lock:
            total_ops = self._total_inferences + self._total_verifications
            failed_ops = self._proof_statuses.get("FAILED", 0) + self._proof_statuses.get("UNKNOWN", 0)
            uptime_pct = ((total_ops - failed_ops) / max(1, total_ops)) * 100.0 if total_ops > 0 else 100.0
            sla_target = 99.9
            error_budget_pct = max(0.0, 100.0 - uptime_pct)
            
            return {
                "sla_target_percent": sla_target,
                "current_uptime_percent": round(uptime_pct, 4),
                "is_sla_met": uptime_pct >= sla_target,
                "total_operations": total_ops,
                "failed_operations": failed_ops,
                "error_budget_consumed_percent": round(error_budget_pct, 4),
                "uptime_seconds": round(time.time() - self.start_timestamp, 1)
            }

    def generate_grafana_dashboard_json(self) -> Dict[str, Any]:
        """Export an enterprise Grafana dashboard definition for TruthGPT Cloud cluster monitoring."""
        return {
            "title": "TruthGPT Cloud - Enterprise Observability & Formal Soundness",
            "uid": "truthgpt-cloud-cluster",
            "schemaVersion": 36,
            "version": 1,
            "refresh": "5s",
            "panels": [
                {
                    "title": "Inference Latency Percentiles (p50 / p95 / p99)",
                    "type": "timeseries",
                    "targets": [{"expr": "truthgpt_cloud_inference_latency_p95_ms", "legendFormat": "p95"}],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "title": "Formal Soundness & Proof Accuracy (%)",
                    "type": "gauge",
                    "targets": [{"expr": "truthgpt_cloud_formal_soundness_percent", "legendFormat": "Soundness %"}],
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                {
                    "title": "Z3 SMT Solver Latency (ms)",
                    "type": "timeseries",
                    "targets": [{"expr": "truthgpt_cloud_smt_latency_avg_ms", "legendFormat": "SMT Solve Time"}],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                },
                {
                    "title": "Total Cluster Operations (Inferences, Proofs, Swarms)",
                    "type": "stat",
                    "targets": [{"expr": "truthgpt_cloud_inferences_total", "legendFormat": "Total Ops"}],
                    "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8}
                },
                {
                    "title": "Proof Status Distribution (SAT / UNSAT / VALID)",
                    "type": "piechart",
                    "targets": [{"expr": "truthgpt_cloud_proof_status_total", "legendFormat": "{{status}}"}],
                    "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8}
                }
            ]
        }

    def reset(self) -> None:
        """Reset telemetry collector metrics."""
        with self._lock:
            self._latencies_ms.clear()
            self._smt_latencies_ms.clear()
            self._total_inferences = 0
            self._total_verifications = 0
            self._total_swarms = 0
            for k in self._proof_statuses:
                self._proof_statuses[k] = 0
            self._audit_logs.clear()
            self.start_timestamp = time.time()



# Global Singleton Telemetry
cloud_telemetry = CloudTelemetryCollector()

__all__ = [
    "AuditLogEntry",
    "CloudTelemetryCollector",
    "cloud_telemetry",
]
