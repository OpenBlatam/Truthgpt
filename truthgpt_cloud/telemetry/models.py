"""
📊 TruthGPT Cloud - Telemetry & Observability Data Models
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Callable


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


__all__ = [
    "AuditLogEntry",
    "AlertRule",
]
