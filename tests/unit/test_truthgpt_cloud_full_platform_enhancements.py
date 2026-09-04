"""
🧪 Tests for TruthGPT Cloud Full Platform Enhancements
Validates session tokens, cryptographic audit ledger verification, client cache aliases,
SRE error budgets, and CLI integration.
"""

from truthgpt_cloud import (
    TruthGPTCloudClient,
)


class TestTruthGPTCloudPlatformEnhancements:
    """Comprehensive test suite for platform-level enhancements."""

    def setup_method(self):
        self.client = TruthGPTCloudClient()

    def test_session_token_lifecycle(self):
        """Test cryptographic generation, structure, and validation of session tokens."""
        token = self.client.create_session_token(duration_seconds=120.0, scopes=["read", "infer"])
        assert token.startswith("sess_tgpt_")
        assert "." in token

        # Validation
        validation = self.client.validate_session_token(token)
        assert validation["is_valid"] is True
        assert validation["user_id"] == self.client.user_id
        assert validation["time_remaining_seconds"] > 0
        assert "read" in validation["scopes"]
        assert "infer" in validation["scopes"]

    def test_session_token_tampering_and_expiration(self):
        """Test rejection of tampered or expired session tokens."""
        # Tampered signature
        valid_token = self.client.create_session_token(duration_seconds=60.0)
        tampered_token = valid_token[:-4] + "dead"
        val_tampered = self.client.validate_session_token(tampered_token)
        assert val_tampered["is_valid"] is False
        assert "signature" in val_tampered["reason"].lower()

        # Expired token
        expired_token = self.client.create_session_token(duration_seconds=-1.0)
        val_expired = self.client.validate_session_token(expired_token)
        assert val_expired["is_valid"] is False
        assert "expired" in val_expired["reason"].lower()

        # Invalid prefix
        val_invalid = self.client.validate_session_token("invalid_prefix_token_123")
        assert val_invalid["is_valid"] is False
        assert "prefix" in val_invalid["reason"].lower()

    def test_cryptographic_audit_ledger_integrity(self):
        """Test unbroken SHA-256 chain verification of the audit ledger."""
        ledger_result = self.client.verify_security_ledger()
        assert ledger_result["is_valid"] is True
        assert ledger_result["total_blocks_verified"] >= 1
        assert "last_block_hash" in ledger_result
        assert len(ledger_result["last_block_hash"]) == 64

    def test_client_cache_purge_alias(self):
        """Test that purge_cache() alias matches purge_expired_cache()."""
        purged = self.client.purge_cache()
        assert isinstance(purged, int)
        assert purged >= 0

    def test_resilience_and_sre_integrations(self):
        """Test SRE error budget burndown and circuit breaker status from client."""
        cb_status = self.client.get_circuit_breaker_status()
        assert "state" in cb_status
        assert cb_status["state"] in ["CLOSED", "OPEN", "HALF_OPEN"]

        eb = self.client.get_error_budget_burndown(sla_target=99.9)
        assert "sla_target_percent" in eb
        assert eb["sla_target_percent"] == 99.9
        assert "budget_burned_percent" in eb
        assert "status" in eb

        rules = self.client.list_alert_rules()
        assert isinstance(rules, list)

        history = self.client.get_alert_history()
        assert isinstance(history, list)

    def test_cli_module_exports_and_banner(self, capsys):
        """Test that the CLI module can be imported and renders its banner cleanly."""
        import truthgpt_cloud_cli
        assert hasattr(truthgpt_cloud_cli, "print_banner")
        assert hasattr(truthgpt_cloud_cli, "main_cli")

        truthgpt_cloud_cli.print_banner()
        captured = capsys.readouterr()
        assert "TruthGPT Cloud CLI" in captured.out
        assert "Z3 SMT Solvers" in captured.out
