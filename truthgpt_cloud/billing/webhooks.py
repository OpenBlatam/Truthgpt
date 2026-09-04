"""
🔔 TruthGPT Cloud - Webhooks & Event Dispatcher
Dispatches signed HMAC-SHA256 event payloads to developer webhook endpoints.
"""

import time
import hmac
import hashlib
import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger("TruthGPT.CloudWebhooks")


@dataclass
class WebhookSubscription:
    webhook_id: str
    user_id: str
    target_url: str
    subscribed_events: List[str]  # e.g. ["subscription.upgraded", "quota.exceeded", "proof.generated"]
    secret_key: str
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class WebhookEventPayload:
    event_id: str
    event_type: str
    user_id: str
    timestamp: float
    data: Dict[str, Any]
    signature: str = ""


class WebhookManager:
    """
    Manages registration and asynchronous event emission for developer webhooks.
    """

    def __init__(self):
        self._webhooks: Dict[str, WebhookSubscription] = {}
        self._event_logs: List[WebhookEventPayload] = []
        self._listeners: List[Callable[[WebhookEventPayload], None]] = []

    def register_webhook(
        self,
        user_id: str,
        target_url: str,
        subscribed_events: Optional[List[str]] = None
    ) -> WebhookSubscription:
        """Register a new webhook endpoint for a user."""
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        secret = f"whsec_{uuid.uuid4().hex[:24]}"
        events = subscribed_events or ["*"]

        sub = WebhookSubscription(
            webhook_id=webhook_id,
            user_id=user_id,
            target_url=target_url,
            subscribed_events=events,
            secret_key=secret
        )
        self._webhooks[webhook_id] = sub
        logger.info(f"Registered webhook {webhook_id} for user {user_id} -> {target_url}")
        return sub

    def list_user_webhooks(self, user_id: str) -> List[WebhookSubscription]:
        """List active webhooks for a user."""
        return [w for w in self._webhooks.values() if w.user_id == user_id]

    def delete_webhook(self, webhook_id: str) -> bool:
        """Remove a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def emit_event(
        self,
        event_type: str,
        user_id: str,
        data: Dict[str, Any],
        custom_secret: Optional[str] = None
    ) -> WebhookEventPayload:
        """
        Emit and sign an event payload.
        """
        event_id = f"evt_{uuid.uuid4().hex[:14]}"
        now = time.time()

        # Build canonical payload for signature
        payload_data = {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": now,
            "data": data
        }

        # Calculate HMAC signature
        canonical = json.dumps(payload_data, sort_keys=True)
        secret = (custom_secret or "tgpt_global_webhook_secret").encode()
        sig = hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()

        event = WebhookEventPayload(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            timestamp=now,
            data=data,
            signature=f"sha256={sig}"
        )

        self._event_logs.append(event)
        if len(self._event_logs) > 1000:
            self._event_logs = self._event_logs[-1000:]

        # Dispatch to any in-process listeners
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in webhook listener: {e}")

        return event

    @staticmethod
    def verify_webhook_signature(
        payload_data: Dict[str, Any],
        signature_header: str,
        secret: str = "tgpt_global_webhook_secret"
    ) -> bool:
        """Verify the HMAC-SHA256 signature of an incoming webhook event."""
        if signature_header.startswith("sha256="):
            signature_header = signature_header[7:]
        canonical = json.dumps(payload_data, sort_keys=True)
        expected_sig = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature_header, expected_sig)

    def get_recent_events(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent event history."""
        events = self._event_logs
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        return [asdict(e) for e in events[-limit:]]


# Global Webhook Manager Instance
webhook_manager = WebhookManager()

__all__ = [
    "WebhookSubscription",
    "WebhookEventPayload",
    "WebhookManager",
    "webhook_manager",
]
