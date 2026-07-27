import hashlib
import hmac
import json
import time
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request

from ..schemas import WebhookPayload
from ..dependencies import WEBHOOK_HMAC_SECRET, WEBHOOK_TIMESTAMP_WINDOW

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def verify_webhook(secret: str, payload: bytes, header: str) -> bool:
    try:
        parts = dict(s.split("=") for s in header.split(","))
        timestamp = int(parts.get("t", 0))
        signature = parts.get("v1", "")
        
        now = int(time.time())
        if abs(now - timestamp) > WEBHOOK_TIMESTAMP_WINDOW:
            return False
        
        message = f"{timestamp}.".encode() + payload
        expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

@router.post("/ingest")
async def webhook_ingest(
    payload: WebhookPayload,
    request: Request,
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(None, alias="X-Timestamp"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    payload_bytes = json.dumps(payload.dict(), sort_keys=True).encode()
    timestamp = int(x_timestamp) if x_timestamp else int(time.time())
    header = f"t={timestamp},v1={x_signature}"
    
    if not verify_webhook(WEBHOOK_HMAC_SECRET, payload_bytes, header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    return {
        "success": True,
        "id": payload.id,
        "received_at": int(time.time())
    }
