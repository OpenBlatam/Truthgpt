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


@dataclass
class WebhookDeliveryAttempt:
    attempt_id: str
    webhook_id: str
    event_id: str
    target_url: str
    status_code: Optional[int]
    success: bool
    attempt_number: int
    timestamp: float = field(default_factory=time.time)
    error_message: Optional[str] = None
    response_body: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebhookManager:
    """
    Manages registration, asynchronous event emission, exponential retry,
    and Dead Letter Queue (DLQ) processing for developer webhooks.
    """

    def __init__(self):
        self._webhooks: Dict[str, WebhookSubscription] = {}
        self._event_logs: List[WebhookEventPayload] = []
        self._listeners: List[Callable[[WebhookEventPayload], None]] = []
        self._dlq: List[WebhookDeliveryAttempt] = []
        self._delivery_history: List[WebhookDeliveryAttempt] = []

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

    def deliver_event_with_retry(
        self,
        event: WebhookEventPayload,
        webhook: WebhookSubscription,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.02,
        dispatcher_fn: Optional[Callable[[str, Dict[str, Any], str], Any]] = None,
    ) -> WebhookDeliveryAttempt:
        """
        Attempt delivery of a webhook event with exponential backoff.
        If all retries fail, routes the attempt to the Dead Letter Queue (DLQ).
        """
        last_status: Optional[int] = None
        last_error: Optional[str] = None
        last_body: Optional[str] = None
        attempt_id = f"att_{uuid.uuid4().hex[:12]}"

        for attempt_num in range(1, max_retries + 1):
            try:
                if dispatcher_fn:
                    res = dispatcher_fn(webhook.target_url, event.data, event.signature)
                    if isinstance(res, tuple):
                        status_code, body = res[0], str(res[1])
                    elif isinstance(res, int):
                        status_code, body = res, "OK"
                    else:
                        status_code, body = 200, str(res)
                else:
                    if not webhook.target_url or "fail" in webhook.target_url:
                        raise ConnectionError(f"Simulated connection failure to {webhook.target_url}")
                    status_code, body = 200, "OK"

                last_status = status_code
                last_body = body
                if 200 <= status_code < 300:
                    attempt = WebhookDeliveryAttempt(
                        attempt_id=attempt_id,
                        webhook_id=webhook.webhook_id,
                        event_id=event.event_id,
                        target_url=webhook.target_url,
                        status_code=status_code,
                        success=True,
                        attempt_number=attempt_num,
                        response_body=body,
                    )
                    self._delivery_history.append(attempt)
                    return attempt
                else:
                    last_error = f"HTTP status {status_code}: {body}"
            except Exception as e:
                last_error = str(e)

            if attempt_num < max_retries:
                sleep_dur = backoff_base_seconds * (2 ** (attempt_num - 1))
                time.sleep(sleep_dur)

        # All attempts failed -> route to Dead Letter Queue (DLQ)
        failed_attempt = WebhookDeliveryAttempt(
            attempt_id=attempt_id,
            webhook_id=webhook.webhook_id,
            event_id=event.event_id,
            target_url=webhook.target_url,
            status_code=last_status,
            success=False,
            attempt_number=max_retries,
            error_message=last_error,
            response_body=last_body,
        )
        self._dlq.append(failed_attempt)
        self._delivery_history.append(failed_attempt)
        logger.warning(f"Webhook {webhook.webhook_id} delivery failed after {max_retries} attempts -> Routed to DLQ")
        return failed_attempt

    def get_dlq_entries(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent dead letter queue entries, optionally filtered by user_id."""
        entries = self._dlq
        if user_id:
            entries = [
                a for a in entries
                if (wh := self._webhooks.get(a.webhook_id)) and wh.user_id == user_id
            ]
        return [a.to_dict() for a in entries[-limit:]]


    def retry_dlq_entry(
        self,
        attempt_id: str,
        dispatcher_fn: Optional[Callable[[str, Dict[str, Any], str], Any]] = None,
    ) -> bool:
        """Reprocess and retry a failed attempt from the DLQ."""
        entry = next((e for e in self._dlq if e.attempt_id == attempt_id), None)
        if not entry:
            return False

        webhook = self._webhooks.get(entry.webhook_id)
        if not webhook:
            return False

        event = next((ev for ev in self._event_logs if ev.event_id == entry.event_id), None)
        if not event:
            event = WebhookEventPayload(
                event_id=entry.event_id,
                event_type="dlq.retry",
                user_id=webhook.user_id,
                timestamp=time.time(),
                data={"retry_from_dlq": True},
            )

        new_attempt = self.deliver_event_with_retry(
            event=event,
            webhook=webhook,
            max_retries=1,
            dispatcher_fn=dispatcher_fn,
        )
        if new_attempt.success:
            self._dlq = [e for e in self._dlq if e.attempt_id != attempt_id]
            return True
        return False

    replay_dlq_entry = retry_dlq_entry

    def clear_dlq(self) -> int:
        """Flush the Dead Letter Queue, returning the count of cleared entries."""
        count = len(self._dlq)
        self._dlq.clear()
        return count

    def get_delivery_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve delivery attempt history."""
        return [a.to_dict() for a in self._delivery_history[-limit:]]


# Aliases for architectural naming
DeadLetterEntry = WebhookDeliveryAttempt

# Global Webhook Manager Instance
webhook_manager = WebhookManager()

__all__ = [
    "WebhookSubscription",
    "WebhookEventPayload",
    "WebhookDeliveryAttempt",
    "DeadLetterEntry",
    "WebhookManager",
    "webhook_manager",
]

