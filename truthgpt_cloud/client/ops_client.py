"""
⚙️ TruthGPT Cloud - Client Operations Mixin
Provides webhooks, telemetry, caching, health diagnostics, resilience, and security audit client methods.
"""

from typing import Dict, List, Optional, Any


class ClientOpsMixin:
    """Mixin encapsulating operational, telemetry, health, webhook, resilience, and security methods."""

    # ---------------------------------------------------------------------------
    # 🔔 Webhooks API
    # ---------------------------------------------------------------------------

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List registered webhooks for current user."""
        from dataclasses import asdict
        return [asdict(w) for w in self.webhooks.list_user_webhooks(self.user_id)]

    def register_webhook(
        self,
        target_url: str,
        subscribed_events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Register a new developer webhook URL."""
        from dataclasses import asdict
        sub = self.webhooks.register_webhook(self.user_id, target_url, subscribed_events)
        return asdict(sub)

    def delete_webhook(self, webhook_id: str) -> bool:
        """Remove a registered webhook."""
        return self.webhooks.delete_webhook(webhook_id)

    def trigger_webhook_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit a synthetic webhook event for testing."""
        from dataclasses import asdict
        evt = self.webhooks.emit_event(event_type, self.user_id, data)
        return asdict(evt)

    # ---------------------------------------------------------------------------
    # 🔒 Cryptographic Audit Ledger & Security APIs
    # ---------------------------------------------------------------------------

    def get_audit_ledger(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent immutable SHA-256 hash-chained audit ledger blocks."""
        from ..security import cloud_security
        return cloud_security.get_audit_ledger(limit=limit)

    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """Verify unbroken cryptographic SHA-256 chain of the audit ledger."""
        from ..security import cloud_security
        return cloud_security.verify_ledger_integrity()

    # ---------------------------------------------------------------------------
    # 📊 Telemetry & Proof Cache APIs
    # ---------------------------------------------------------------------------

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Get live cluster telemetry, percentiles and verification soundness rates."""
        return self.telemetry.get_cluster_metrics()

    def get_telemetry_stats(self) -> Dict[str, Any]:
        """Alias for get_telemetry_metrics."""
        return self.get_telemetry_metrics()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get semantic proof cache statistics and compute savings."""
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Clear the proof cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics combining user quota, telemetry, and proof cache."""
        user = self.sub_manager.get_user(self.user_id)
        quota_data = user.to_dict() if user else {}
        return {
            "tier": self.tier.value,
            "user_id": self.user_id,
            "quota_usage": quota_data.get("usage", {}),
            "cache": self.get_cache_stats(),
            "telemetry": self.get_telemetry_metrics()
        }

    def get_sla_metrics(self) -> Dict[str, Any]:
        """Get real-time SLA metrics and error budget status."""
        return self.telemetry.get_sla_status()

    def export_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate ready-to-import Grafana dashboard JSON."""
        return self.telemetry.generate_grafana_dashboard_json()

    def get_health_status(self) -> Dict[str, Any]:
        """Check operational readiness and health of all cloud components."""
        return self.telemetry.get_health_status()

    # ---------------------------------------------------------------------------
    # ⚡ Resilience & Fault Tolerance APIs
    # ---------------------------------------------------------------------------

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get the current state and operational metrics of the inference circuit breaker."""
        if hasattr(self.router, "_circuit_breaker"):
            return self.router._circuit_breaker.get_status()
        return {"state": "CLOSED", "status": "unavailable"}

    def reset_circuit_breaker(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Reset the inference circuit breaker to CLOSED state."""
        if hasattr(self.router, "_circuit_breaker"):
            self.router._circuit_breaker.reset()
        return {"success": True, "message": "Circuit breaker reset to CLOSED state"}

    # ---------------------------------------------------------------------------
    # 🚨 SRE Alerting & Error Budget APIs
    # ---------------------------------------------------------------------------

    def register_alert_rule(
        self,
        name: str,
        metric_key: str,
        threshold: float,
        comparison: str = "gte",
        callback: Optional[Any] = None,
        cooldown_seconds: float = 60.0
    ):
        """Register an automated alerting rule evaluated on each metric event."""
        return self.telemetry.register_alert_rule(
            name=name,
            metric_key=metric_key,
            threshold=threshold,
            comparison=comparison,
            callback=callback,
            cooldown_seconds=cooldown_seconds
        )

    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """List all active alert rules."""
        return self.telemetry.list_alert_rules()

    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent alert trigger events."""
        return self.telemetry.get_alert_history(limit=limit)

    def get_error_budget_burndown(self, sla_target: float = 99.9) -> Dict[str, Any]:
        """Calculate detailed error budget burndown and projected exhaustion."""
        return self.telemetry.get_error_budget_burndown(sla_target=sla_target)

    def purge_expired_cache(self) -> int:
        """Manually purge expired entries from the semantic proof cache."""
        return self.cache.purge_expired()

    # ---------------------------------------------------------------------------
    # 🔒 Cryptographic Security & Session Management
    # ---------------------------------------------------------------------------

    def create_session_token(
        self,
        duration_seconds: float = 3600.0,
        scopes: Optional[List[str]] = None
    ) -> str:
        """Generate a cryptographically signed temporary session token for the current user."""
        return self.security.generate_session_token(
            self.user_id,
            duration_seconds=duration_seconds,
            scopes=scopes
        )

    def validate_session_token(self, token: str) -> Dict[str, Any]:
        """Validate signature and expiration of a cryptographic session token."""
        return self.security.validate_session_token(token)

    def verify_security_ledger(self) -> Dict[str, Any]:
        """Verify the unbroken cryptographic SHA-256 chain of the security audit ledger."""
        return self.security.verify_ledger_integrity()

    def export_database_backup(self, backup_dir: Optional[str] = None) -> str:
        """Create a point-in-time backup snapshot of the subscriptions database."""
        return self.sub_manager.export_backup(backup_dir=backup_dir)

    def database_health(self) -> Dict[str, Any]:
        """Validate database integrity and return diagnostic status."""
        return self.sub_manager.validate_database_integrity()

    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive readiness and subsystem health check."""
        from ..core.health import cloud_health_checker
        res = cloud_health_checker.check_readiness()
        if isinstance(res, dict):
            return res
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)

    def get_platform_diagnostics(self) -> Dict[str, Any]:
        """Inspect runtime environment, hardware resources, solvers, and platform metrics."""
        from ..core.health import cloud_health_checker
        res = cloud_health_checker.get_platform_diagnostics()
        if isinstance(res, dict):
            return res
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)

    def check_liveness(self) -> bool:
        """Lightweight ping probe for Kubernetes liveness."""
        from ..core.health import cloud_health_checker
        return cloud_health_checker.check_liveness()

    def check_readiness(self) -> Dict[str, Any]:
        """Deep readiness probe evaluating critical subsystems."""
        from ..core.health import cloud_health_checker
        res = cloud_health_checker.check_readiness()
        if isinstance(res, dict):
            return res
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)

    def audit_secrets(self, required_keys: Optional[List[str]] = None) -> Dict[str, bool]:
        """Audit the configuration status of essential secrets without disclosing sensitive values."""
        from ..core.secrets import cloud_secrets
        return cloud_secrets.audit_secrets_presence(required_keys=required_keys)

    # ---------------------------------------------------------------------------
    # 📬 Webhook Dead Letter Queue (DLQ)
    # ---------------------------------------------------------------------------

    def get_webhook_dlq(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent failed webhook delivery attempts in the DLQ."""
        return self.webhooks.get_dlq_entries(limit=limit)

    def retry_webhook_dlq(
        self,
        attempt_id: str,
        dispatcher_fn: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Retry a failed webhook delivery attempt from the DLQ."""
        success = self.webhooks.retry_dlq_entry(attempt_id=attempt_id, dispatcher_fn=dispatcher_fn)
        return {"success": success, "attempt_id": attempt_id}

    def clear_webhook_dlq(self) -> int:
        """Flush the Dead Letter Queue, returning the count of cleared entries."""
        return self.webhooks.clear_dlq()

    # Aliases
    purge_cache = purge_expired_cache


__all__ = ["ClientOpsMixin"]
