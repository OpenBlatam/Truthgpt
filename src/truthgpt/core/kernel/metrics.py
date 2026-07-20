"""
TruthGPT Kernel Metrics — Real-time command and system telemetry.
Tracks command usage, latency, errors, and system health over time.
"""
import time
import threading
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class CommandMetric:
    command: str
    success: bool
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


@dataclass
class SystemSnapshot:
    timestamp: float
    cpu_percent: float
    memory_mb: float
    active_tasks: int


class KernelMetrics:
    """
    Thread-safe metrics collector for the TruthGPT Kernel.
    Stores rolling windows of command executions and system snapshots.
    """

    MAX_HISTORY = 500

    def __init__(self):
        self._lock = threading.Lock()
        self._command_history: deque = deque(maxlen=self.MAX_HISTORY)
        self._system_snapshots: deque = deque(maxlen=100)
        self._command_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._total_commands = 0
        self._total_errors = 0
        self._start_time = time.time()

    # ------------------------------------------------------------------ #
    #  Recording                                                           #
    # ------------------------------------------------------------------ #

    def record_command(self, command: str, success: bool,
                       latency_ms: float, error: Optional[str] = None):
        """Record a single command execution."""
        metric = CommandMetric(
            command=command,
            success=success,
            latency_ms=latency_ms,
            error=error,
        )
        with self._lock:
            self._command_history.append(metric)
            self._command_counts[command] += 1
            self._total_commands += 1
            if not success:
                self._error_counts[command] += 1
                self._total_errors += 1

    def record_system_snapshot(self, cpu: float, memory_mb: float,
                               active_tasks: int = 0):
        """Record a system resource snapshot."""
        snap = SystemSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu,
            memory_mb=memory_mb,
            active_tasks=active_tasks,
        )
        with self._lock:
            self._system_snapshots.append(snap)

    # ------------------------------------------------------------------ #
    #  Queries                                                             #
    # ------------------------------------------------------------------ #

    def get_summary(self) -> Dict[str, Any]:
        """Return a high-level summary dict."""
        with self._lock:
            uptime_s = time.time() - self._start_time
            recent = list(self._command_history)[-50:]
            avg_latency = (
                sum(m.latency_ms for m in recent) / len(recent)
                if recent else 0.0
            )
            error_rate = (
                self._total_errors / self._total_commands
                if self._total_commands else 0.0
            )
            top_commands = sorted(
                self._command_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
            return {
                "uptime_seconds": round(uptime_s, 1),
                "total_commands": self._total_commands,
                "total_errors": self._total_errors,
                "error_rate_pct": round(error_rate * 100, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "top_commands": top_commands,
            }

    def get_recent_errors(self, n: int = 10) -> List[CommandMetric]:
        """Return the last N failed commands."""
        with self._lock:
            return [
                m for m in reversed(self._command_history)
                if not m.success
            ][:n]

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Return p50/p90/p99 latency from recent history."""
        with self._lock:
            latencies = sorted(m.latency_ms for m in self._command_history)
        if not latencies:
            return {"p50": 0.0, "p90": 0.0, "p99": 0.0}
        n = len(latencies)
        return {
            "p50": latencies[int(n * 0.50)],
            "p90": latencies[int(n * 0.90)],
            "p99": latencies[min(int(n * 0.99), n - 1)],
        }

    def reset(self):
        """Clear all collected metrics."""
        with self._lock:
            self._command_history.clear()
            self._system_snapshots.clear()
            self._command_counts.clear()
            self._error_counts.clear()
            self._total_commands = 0
            self._total_errors = 0
            self._start_time = time.time()


# Module-level singleton
_kernel_metrics: Optional[KernelMetrics] = None


def get_metrics() -> KernelMetrics:
    global _kernel_metrics
    if _kernel_metrics is None:
        _kernel_metrics = KernelMetrics()
    return _kernel_metrics
