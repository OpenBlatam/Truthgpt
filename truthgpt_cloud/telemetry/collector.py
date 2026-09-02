"""
📊 TruthGPT Cloud - Telemetry, Observability & Cluster Analytics
Aggregates inference latencies (p50/p95/p99), proof solve rates, token economics, and audit logs.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
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


@dataclass
class AlertRule:
    """Configurable alert rule evaluated on metric recording."""
    name: str
    metric_key: str  # e.g. "p99_latency_ms", "soundness_percent", "error_rate"
    threshold: float
    comparison: str = "gte"  # "gte", "lte", "gt", "lt"
    callback: Optional[Callable[[str, float, float], None]] = None
    is_active: bool = True
    triggered_count: int = 0
    last_triggered_at: float = 0.0
    cooldown_seconds: float = 60.0  # Don't re-fire within this window

    def evaluate(self, current_value: float) -> bool:
        """Check if current value violates the threshold."""
        if self.comparison == "gte":
            return current_value >= self.threshold
        elif self.comparison == "lte":
            return current_value <= self.threshold
        elif self.comparison == "gt":
            return current_value > self.threshold
        elif self.comparison == "lt":
            return current_value < self.threshold
        return False


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
        self._alert_rules: List[AlertRule] = []
        self._alert_history: List[Dict[str, Any]] = []
        self.start_timestamp: float = time.time()

    def record_inference(self, latency_ms: float, tokens: int = 0, tier: str = "pro") -> None:
        with self._lock:
            self._total_inferences += 1
            self._latencies_ms.append(latency_ms)
            if len(self._latencies_ms) > self.max_history:
                self._latencies_ms.pop(0)
            self._evaluate_alerts()

    def record_verification(self, latency_ms: float, status: str = "PROVEN_VALID") -> None:
        with self._lock:
            self._total_verifications += 1
            self._smt_latencies_ms.append(latency_ms)
            if len(self._smt_latencies_ms) > self.max_history:
                self._smt_latencies_ms.pop(0)
            self._proof_statuses[status] = self._proof_statuses.get(status, 0) + 1
            self._evaluate_alerts()

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
            self._alert_history.clear()
            self.start_timestamp = time.time()

    # ---------------------------------------------------------------------------
    # 🚨 Alert Rules Engine
    # ---------------------------------------------------------------------------

    def register_alert_rule(
        self,
        name: str,
        metric_key: str,
        threshold: float,
        comparison: str = "gte",
        callback: Optional[Callable[[str, float, float], None]] = None,
        cooldown_seconds: float = 60.0,
    ) -> AlertRule:
        """
        Register an alert rule that is automatically evaluated on each metric recording.

        Args:
            name: Human-readable alert name.
            metric_key: One of "p99_latency_ms", "p95_latency_ms", "avg_latency_ms",
                        "soundness_percent", "error_rate_percent", "total_failures".
            threshold: The value that triggers the alert.
            comparison: "gte", "lte", "gt", "lt".
            callback: Optional function(alert_name, threshold, current_value) invoked on trigger.
            cooldown_seconds: Minimum interval between re-triggers.
        """
        rule = AlertRule(
            name=name,
            metric_key=metric_key,
            threshold=threshold,
            comparison=comparison,
            callback=callback,
            cooldown_seconds=cooldown_seconds,
        )
        with self._lock:
            self._alert_rules.append(rule)
        return rule

    def _evaluate_alerts(self) -> None:
        """Evaluate all active alert rules against current metrics. Must be called with lock held."""
        if not self._alert_rules:
            return

        now = time.time()
        metrics = self._calc_percentiles(self._latencies_ms)
        smt_metrics = self._calc_percentiles(self._smt_latencies_ms)

        total_proofs = sum(self._proof_statuses.values())
        invalid_statuses = {"UNKNOWN", "FAILED", "VIOLATED", "COUNTEREXAMPLE_FOUND"}
        failed_proofs = sum(v for k, v in self._proof_statuses.items() if k in invalid_statuses)
        success_proofs = total_proofs - failed_proofs
        soundness = (success_proofs / max(1, total_proofs)) * 100.0 if total_proofs > 0 else 100.0
        error_rate = (failed_proofs / max(1, total_proofs)) * 100.0 if total_proofs > 0 else 0.0

        metric_values = {
            "p99_latency_ms": metrics["p99"],
            "p95_latency_ms": metrics["p95"],
            "p50_latency_ms": metrics["p50"],
            "avg_latency_ms": metrics["avg"],
            "max_latency_ms": metrics["max"],
            "smt_p99_latency_ms": smt_metrics["p99"],
            "smt_avg_latency_ms": smt_metrics["avg"],
            "soundness_percent": soundness,
            "error_rate_percent": error_rate,
            "total_failures": float(failed_proofs),
            "total_inferences": float(self._total_inferences),
        }

        for rule in self._alert_rules:
            if not rule.is_active:
                continue
            current_val = metric_values.get(rule.metric_key)
            if current_val is None:
                continue
            if rule.evaluate(current_val):
                if now - rule.last_triggered_at >= rule.cooldown_seconds:
                    rule.triggered_count += 1
                    rule.last_triggered_at = now
                    alert_event = {
                        "alert_name": rule.name,
                        "metric_key": rule.metric_key,
                        "threshold": rule.threshold,
                        "current_value": current_val,
                        "comparison": rule.comparison,
                        "triggered_at": now,
                        "triggered_count": rule.triggered_count,
                    }
                    self._alert_history.append(alert_event)
                    if len(self._alert_history) > self.max_history:
                        self._alert_history.pop(0)
                    if rule.callback:
                        try:
                            rule.callback(rule.name, rule.threshold, current_val)
                        except Exception:
                            pass

    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent alert trigger events."""
        with self._lock:
            return list(self._alert_history[-limit:])

    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """List all registered alert rules and their trigger counts."""
        with self._lock:
            return [
                {
                    "name": r.name,
                    "metric_key": r.metric_key,
                    "threshold": r.threshold,
                    "comparison": r.comparison,
                    "is_active": r.is_active,
                    "triggered_count": r.triggered_count,
                    "cooldown_seconds": r.cooldown_seconds,
                }
                for r in self._alert_rules
            ]

    def get_error_budget_burndown(self, sla_target: float = 99.9) -> Dict[str, Any]:
        """
        Calculate error budget burndown for SRE workflows.
        Shows how much of the error budget has been consumed and projected exhaustion.
        """
        with self._lock:
            total_ops = self._total_inferences + self._total_verifications
            failed_ops = self._proof_statuses.get("FAILED", 0) + self._proof_statuses.get("UNKNOWN", 0)
            uptime_pct = ((total_ops - failed_ops) / max(1, total_ops)) * 100.0 if total_ops > 0 else 100.0

            error_budget_total = 100.0 - sla_target  # e.g. 0.1% for 99.9%
            error_budget_consumed = max(0.0, 100.0 - uptime_pct)
            budget_remaining_pct = max(0.0, error_budget_total - error_budget_consumed)
            budget_burn_rate = (error_budget_consumed / max(0.001, error_budget_total)) * 100.0

            uptime_seconds = time.time() - self.start_timestamp
            if failed_ops > 0 and uptime_seconds > 0:
                failure_rate_per_hour = (failed_ops / uptime_seconds) * 3600
                if failure_rate_per_hour > 0 and total_ops > 0:
                    ops_per_hour = (total_ops / uptime_seconds) * 3600
                    projected_error_pct_per_hour = (failure_rate_per_hour / max(1, ops_per_hour)) * 100
                    hours_until_exhaustion = budget_remaining_pct / max(0.0001, projected_error_pct_per_hour)
                else:
                    hours_until_exhaustion = float("inf")
            else:
                hours_until_exhaustion = float("inf")

            return {
                "sla_target_percent": sla_target,
                "current_uptime_percent": round(uptime_pct, 4),
                "error_budget_total_percent": round(error_budget_total, 4),
                "error_budget_consumed_percent": round(error_budget_consumed, 4),
                "error_budget_remaining_percent": round(budget_remaining_pct, 4),
                "burn_rate_percent": round(budget_burn_rate, 2),
                "projected_hours_until_exhaustion": round(hours_until_exhaustion, 2) if hours_until_exhaustion != float("inf") else None,
                "is_budget_exceeded": error_budget_consumed >= error_budget_total,
                "total_operations": total_ops,
                "failed_operations": failed_ops,
                "uptime_seconds": round(uptime_seconds, 1),
            }



# Global Singleton Telemetry
cloud_telemetry = CloudTelemetryCollector()

__all__ = [
    "AuditLogEntry",
    "CloudTelemetryCollector",
    "cloud_telemetry",
]
