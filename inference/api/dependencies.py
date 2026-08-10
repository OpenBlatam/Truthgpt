import os
from collections import defaultdict
from typing import Any, Dict, Optional
from fastapi import Header, HTTPException, status
from ..middleware.cache_manager import CacheManager

API_TOKEN = os.environ.get("TRUTHGPT_API_TOKEN", "changeme")
WEBHOOK_HMAC_SECRET = os.environ.get("WEBHOOK_HMAC_SECRET", "changeme-secret")
WEBHOOK_TIMESTAMP_WINDOW = int(os.environ.get("WEBHOOK_TIMESTAMP_WINDOW", "300"))

class GlobalState:
    """Global application state"""
    def __init__(self):
        self.model: Optional[Any] = None
        self.cache: Optional[CacheManager] = None
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.batch_processor = None

state = GlobalState()

def get_global_state() -> GlobalState:
    """Returns global application state instance."""
    return state

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify API token"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token
