from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class MemoryEntry:
    id: Optional[int]
    agent_id: str
    key: str
    value: str
    timestamp: Optional[datetime] = None

@dataclass
class SecurityEvent:
    id: Optional[int]
    event_type: str
    details: str
    timestamp: Optional[datetime] = None
