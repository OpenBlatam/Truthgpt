"""
📊 TruthGPT Cloud - Telemetry & Observability Data Models
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class AuditLogEntry:
    timestamp: float
    event_type: str  # "signup", "upgrade", "key_generated", "quota_warning", "verification"
    user_id: str
    details: Dict[str, Any]


__all__ = ["AuditLogEntry"]
