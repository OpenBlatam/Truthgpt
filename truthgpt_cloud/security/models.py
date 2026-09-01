"""
🔒 TruthGPT Cloud - Security & Key Metadata Models
"""

import time
from dataclasses import dataclass, field
from typing import Set, Optional, List
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


__all__ = ["ApiKeyMetadata"]
