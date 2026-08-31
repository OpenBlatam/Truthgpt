"""
📊 TruthGPT Cloud - Telemetry, Observability & Cluster Analytics
Aggregates inference latencies (p50/p95/p99), proof solve rates, token economics, and audit logs.
"""

import time
import math
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class AuditLogEntry:
    timestamp: float
    event_type: str  # "signup", "upgrade", "key_generated", "quota_warning", "verification"
    user_id: str
    details: Dict[str, Any]


class CloudTelemetryCollector:
    """
    Real-time telemetry and monitoring collector for TruthGPT Cloud.
    """

    def __init__(self, max_history: int = 1000):
        self._lock = threading.RLock()
        self.max_history = max_history
        self._latencies_ms: List[float] = []
        self._smt_latencies_ms: List[float] = []
        self._total_inferences: int = 0
        self._total_verifications: int = 0
        self._total_swarms: int = 0
        self._proof_statuses: Dict[str, int] = {
            "PROVEN_SAT": 0,
            "PROVEN_UNSAT": 0,
            "VERIFIED_SYMBOLIC": 0,
            "UNKNOWN": 0,
            "FAILED": 0
        }
        self._audit_logs: List[AuditLogEntry] = []
        self.start_timestamp: float = time.time()

    def record_inference(self, latency_ms: float, tokens: int, tier: str) -> None:
        with self._lock:
            self._total_inferences += 1
            self._latencies_ms.append(latency_ms)
            if len(self._latencies_ms) > self.max_history:
                self._latencies_ms.pop(0)

    def record_verification(self, latency_ms: float, status: str) -> None:
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
            entry = AuditLogEntry(timestamp=time.time(), event_type=event_type, user_id=user_id, details=details)
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
            "max": round(s[-1], 2)
        }

    def get_cluster_metrics(self) -> Dict[str, Any]:
        with self._lock:
            uptime = round(time.time() - self.start_timestamp, 1)
            total_proofs = sum(self._proof_statuses.values())
            success_proofs = self._proof_statuses.get("PROVEN_SAT", 0) + self._proof_statuses.get("VERIFIED_SYMBOLIC", 0)
            formal_soundness_rate = round((success_proofs / max(1, total_proofs)) * 100, 2)

            return {
                "uptime_seconds": uptime,
                "total_inferences": self._total_inferences,
                "total_verifications": self._total_verifications,
                "total_swarms": self._total_swarms,
                "formal_soundness_percent": formal_soundness_rate,
                "proof_status_distribution": dict(self._proof_statuses),
                "inference_latency_ms": self._calc_percentiles(self._latencies_ms),
                "smt_solver_latency_ms": self._calc_percentiles(self._smt_latencies_ms),
                "active_audits_count": len(self._audit_logs)
            }

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(log) for log in self._audit_logs[-limit:]]


# Global Singleton Telemetry
cloud_telemetry = CloudTelemetryCollector()
