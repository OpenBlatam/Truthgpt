"""
🧪 Unit Test Suite for TruthGPT Cloud Resilience, Circuit Breakers, Alerting & SRE Observability
Validates:
- Circuit Breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Retry with Exponential Backoff & Jitter (sync and async)
- Real-time Alert Rules Engine & metric threshold evaluations
- SRE Error Budget Burndown & SLA calculation
- Semantic Proof Cache dynamic TTL expiration and purge
- JsonFileStorageBackend debounced writes and snapshot safety
- FastAPI resilience and alerting REST endpoints
"""

import time
import pytest
import asyncio
from fastapi.testclient import TestClient

from truthgpt_cloud import (
    TruthGPTCloudClient,
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    retry_with_backoff,
    RetryConfig,
    AlertRule,
    cloud_telemetry,
    proof_cache,
    CachedProofEntry,
    CloudProofCache,
)
from truthgpt_cloud.storage import JsonFileStorageBackend
from truthgpt_cloud_server import app


class TestCircuitBreaker:
    """Test suite for thread-safe CircuitBreaker implementation."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(name="test_cb", failure_threshold=3, recovery_timeout_seconds=0.2)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True
        assert cb.is_open is False
        assert cb.is_half_open is False

    def test_transitions_to_open_after_failures(self):
        cb = CircuitBreaker(name="test_cb_fail", failure_threshold=3, recovery_timeout_seconds=0.2)
        
        for _ in range(3):
            try:
                with cb:
                    raise ValueError("Simulated downstream error")
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN
        assert cb.is_open is True

        # Next call should be rejected immediately by circuit breaker
        with pytest.raises(CircuitBreakerOpen) as excinfo:
            with cb:
                pass
        assert "is OPEN" in str(excinfo.value)
        assert excinfo.value.recovery_time_remaining >= 0.0

    def test_half_open_recovery_to_closed(self):
        cb = CircuitBreaker(
            name="test_recovery",
            failure_threshold=2,
            recovery_timeout_seconds=0.05,
            success_threshold=2,
            half_open_max_calls=2
        )

        for _ in range(2):
            try:
                with cb:
                    raise RuntimeError("Downstream failure")
            except RuntimeError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout to elapse
        time.sleep(0.08)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.is_half_open is True

        # Successful calls in HALF_OPEN state
        with cb:
            pass
        assert cb.state == CircuitState.HALF_OPEN

        with cb:
            pass
        # Reached success_threshold=2, transitions to CLOSED
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True

    def test_force_open_and_reset(self):
        cb = CircuitBreaker(name="test_manual")
        assert cb.is_closed is True

        cb.force_open()
        assert cb.is_open is True

        cb.reset()
        assert cb.is_closed is True
        assert cb.metrics.total_failures == 0

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_context_manager(self):
        cb = CircuitBreaker(name="async_cb", failure_threshold=2, recovery_timeout_seconds=0.1)

        async def failing_call():
            async with cb:
                raise ConnectionResetError("Connection lost")

        for _ in range(2):
            with pytest.raises(ConnectionResetError):
                await failing_call()

        assert cb.is_open is True

        # Call rejected asynchronously
        with pytest.raises(CircuitBreakerOpen):
            async with cb:
                pass


class TestRetryWithBackoff:
    """Test suite for retry_with_backoff decorator."""

    def test_sync_retry_succeeds_eventually(self):
        attempts = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, max_delay=0.05)
        def flaky_function():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Transient network timeout")
            return "SUCCESS"

        result = flaky_function()
        assert result == "SUCCESS"
        assert attempts == 3

    def test_sync_retry_exhausted_raises(self):
        attempts = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal attempts
            attempts += 1
            raise ValueError("Permanent computation error")

        with pytest.raises(ValueError):
            always_fails()
        assert attempts == 3  # initial + 2 retries

    def test_non_retryable_exception_fails_immediately(self):
        attempts = 0

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,),
            non_retryable_exceptions=(KeyError,)
        )
        def selective_fail():
            nonlocal attempts
            attempts += 1
            raise KeyError("Do not retry this")

        with pytest.raises(KeyError):
            selective_fail()
        assert attempts == 1

    @pytest.mark.asyncio
    async def test_async_retry_succeeds(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def async_worker():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Async timeout")
            return 42

        val = await async_worker()
        assert val == 42
        assert call_count == 2


class TestAlertingAndErrorBudget:
    """Test suite for AlertRule, evaluation engine, and error budget burndown."""

    def setup_method(self):
        cloud_telemetry.reset_metrics()

    def test_alert_rule_evaluation_and_trigger(self):
        triggered_events = []

        def on_alert(name, threshold, val):
            triggered_events.append({"name": name, "threshold": threshold, "value": val})

        rule = cloud_telemetry.register_alert_rule(
            name="high_latency_alert",
            metric_key="p99_latency_ms",
            threshold=100.0,
            comparison="gte",
            callback=on_alert,
            cooldown_seconds=0.1
        )
        assert rule.name == "high_latency_alert"
        assert rule.triggered_count == 0

        # Record latencies below threshold
        cloud_telemetry.record_inference(latency_ms=45.0)
        assert len(triggered_events) == 0

        # Record latency exceeding threshold
        cloud_telemetry.record_inference(latency_ms=150.0)
        assert len(triggered_events) >= 1
        assert triggered_events[-1]["name"] == "high_latency_alert"

        # Check history
        history = cloud_telemetry.get_alert_history()
        assert len(history) >= 1
        assert history[-1]["alert_name"] == "high_latency_alert"

    def test_error_budget_burndown_calculation(self):
        # 10 successful verifications
        for _ in range(10):
            cloud_telemetry.record_verification(latency_ms=1.5, status="PROVEN_VALID")

        burndown = cloud_telemetry.get_error_budget_burndown(sla_target=99.9)
        assert burndown["sla_target_percent"] == 99.9
        assert burndown["current_uptime_percent"] == 100.0
        assert burndown["is_budget_exceeded"] is False
        assert burndown["total_operations"] >= 10
        assert burndown["failed_operations"] == 0

        # Introduce failures
        for _ in range(2):
            cloud_telemetry.record_verification(latency_ms=2.0, status="FAILED")

        burndown_after = cloud_telemetry.get_error_budget_burndown(sla_target=99.9)
        assert burndown_after["failed_operations"] >= 2
        assert burndown_after["error_budget_consumed_percent"] > 0.0


class TestProofCacheTTLExpiration:
    """Test suite for semantic proof cache TTL, expiration, and manual purge."""

    def test_cache_entry_ttl_and_expiry(self):
        cache = CloudProofCache(max_entries=50, default_ttl_seconds=0.05, auto_warmup=False)

        claim = "x + 0 = x"
        cert_data = {"status": "PROVEN_VALID", "proof_tree_hash": "0x123"}
        cache.store_proof(claim, cert_data, ttl_seconds=0.05)

        # Immediate retrieval succeeds (HIT)
        proof = cache.get_proof(claim)
        assert proof is not None
        assert proof["status"] == "PROVEN_VALID"

        # Wait for TTL to expire
        time.sleep(0.08)

        # Retrieval after expiry fails (MISS & auto-eviction)
        expired_proof = cache.get_proof(claim)
        assert expired_proof is None

        stats = cache.get_stats()
        assert stats["total_ttl_evictions"] >= 1

    def test_purge_expired_cache(self):
        cache = CloudProofCache(max_entries=50, default_ttl_seconds=0.05, auto_warmup=False)
        cache.store_proof("claim_a", {"status": "PROVEN_VALID"}, ttl_seconds=0.04)
        cache.store_proof("claim_b", {"status": "PROVEN_VALID"}, ttl_seconds=10.0)

        time.sleep(0.06)
        purged = cache.purge_expired()
        assert purged >= 1

        stats = cache.get_stats()
        assert stats["cached_entries"] == 1  # claim_b remains


class TestStorageDebounceAndSnapshot:
    """Test JsonFileStorageBackend debounced writes and atomic snapshots."""

    def test_rapid_writes_and_instant_snapshot(self, tmp_path):
        db_path = str(tmp_path / "debounce_test.json")
        storage = JsonFileStorageBackend(file_path=db_path, debounce_ms=100)

        for i in range(10):
            storage.set("records", f"rec_{i}", {"val": i * 10})

        # Memory cache has all 10
        assert len(storage.get_all("records")) == 10

        # Snapshot forces immediate flush without error
        snap = storage.create_snapshot()
        assert snap is not None
        assert ".snapshot." in snap

        # Another instance loading from disk sees all 10 records
        storage2 = JsonFileStorageBackend(file_path=db_path)
        assert len(storage2.get_all("records")) == 10


class TestClientAndFastAPIResilienceEndpoints:
    """Test SDK methods and FastAPI endpoints for resilience, alerts, and cache."""

    def setup_method(self):
        self.client = TruthGPTCloudClient()
        self.api_client = TestClient(app)

    def test_client_sdk_resilience_methods(self):
        cb_status = self.client.get_circuit_breaker_status()
        assert "state" in cb_status
        assert cb_status["state"] in ["CLOSED", "OPEN", "HALF_OPEN"]

        # Reset
        self.client.reset_circuit_breaker()

        # Error budget burndown from client
        burndown = self.client.get_error_budget_burndown(sla_target=99.9)
        assert "current_uptime_percent" in burndown

        # Cache purge from client
        purged = self.client.purge_expired_cache()
        assert isinstance(purged, int)

    def test_fastapi_resilience_and_alert_endpoints(self):
        # 1. Resilience status
        r_res = self.api_client.get("/api/v1/cloud/resilience/status")
        assert r_res.status_code == 200
        assert r_res.json()["success"] is True

        # 2. Reset circuit breaker
        r_reset = self.api_client.post("/api/v1/cloud/resilience/reset")
        assert r_reset.status_code == 200
        assert r_reset.json()["success"] is True

        # 3. Register alert rule endpoint
        r_reg = self.api_client.post(
            "/api/v1/cloud/telemetry/alerts",
            json={
                "name": "api_test_alert",
                "metric_key": "soundness_percent",
                "threshold": 95.0,
                "comparison": "lte"
            }
        )
        assert r_reg.status_code == 200
        assert r_reg.json()["success"] is True
        assert r_reg.json()["rule"]["name"] == "api_test_alert"

        # 4. List alerts endpoint
        r_list = self.api_client.get("/api/v1/cloud/telemetry/alerts")
        assert r_list.status_code == 200
        assert len(r_list.json()["rules"]) >= 1

        # 5. Error budget endpoint
        r_eb = self.api_client.get("/api/v1/cloud/telemetry/error-budget?sla_target=99.9")
        assert r_eb.status_code == 200
        assert "error_budget" in r_eb.json()

        # 6. Cache purge endpoint
        r_purge = self.api_client.post("/api/v1/cloud/cache/purge")
        assert r_purge.status_code == 200
        assert r_purge.json()["success"] is True
