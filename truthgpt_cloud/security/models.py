"""
🔒 TruthGPT Cloud - Security & Key Metadata Models
"""

import time
from dataclasses import dataclass, field, asdict
from typing import Set, Optional, List, Dict, Any
from .scopes import ApiKeyScope


@dataclass
class ApiKeyMetadata:
    key_id: str
    key_hash: str
    key_prefix: str
    user_id: str
    name: str = "Default Key"
    scopes: Set[ApiKeyScope] = field(default_factory=lambda: {ApiKeyScope.ALL})
    ip_whitelist: Optional[List[str]] = None
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True
    last_used_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["scopes"] = [s.value if hasattr(s, "value") else str(s) for s in self.scopes]
        return d


@dataclass
class LedgerBlock:
    block_index: int
    timestamp: float
    event_type: str
    user_id: str
    details: Dict[str, Any]
    prev_hash: str
    block_hash: str
    asymmetric_signature: Optional[str] = None
    public_key_hex: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = [
    "ApiKeyMetadata",
    "LedgerBlock",
]
