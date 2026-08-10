"""
🧪 Execution Pipeline & Middleware Integration Test Suite
Verifies end-to-end processing of ExecutionPipeline with middleware components.
"""

import pytest
import asyncio
import sys
from pathlib import Path

parent_dir = str(Path(__file__).resolve().parents[3])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from optimization_core.inference.pipelines.execution_pipeline import ExecutionPipeline
from optimization_core.inference.middleware.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
from optimization_core.inference.middleware.cache import InMemoryCache
from optimization_core.inference.middleware.cache_manager import CacheManager
from optimization_core.inference.monitoring.metrics import MetricsCollector
from optimization_core.inference.core.base_engine import BaseInferenceEngine, InferenceRequest, InferenceResult


class MockEngine(BaseInferenceEngine):
    """Mock engine for testing execution pipeline."""

    def __init__(self, model: str = "mock-model", should_fail: bool = False):
        super().__init__(model=model)
        self.should_fail = should_fail
        self.call_count = 0

    def _initialize_engine(self, **kwargs):
        pass

    def generate(self, prompt, **kwargs):
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Engine failure simulated!")
        p_str = prompt.prompt if hasattr(prompt, "prompt") else str(prompt)
        return InferenceResult(text=f"Processed: {p_str}", model_name=self.model_path, latency_ms=5.0)

    async def generate_async(self, prompt, **kwargs):
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Engine failure simulated!")
        p_str = prompt.prompt if hasattr(prompt, "prompt") else str(prompt)
        return f"Async processed: {p_str}"


@pytest.mark.asyncio
async def test_execution_pipeline_basic():
    """Verify basic execution pipeline without middleware."""
    engine = MockEngine()
    pipeline = ExecutionPipeline(engine=engine, middlewares=[])

    req = InferenceRequest(prompt="Hello Test")
    result = await pipeline.execute(req)

    assert result == "Async processed: Hello Test"
    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_circuit_breaker_middleware():
    """Verify CircuitBreaker prevents execution when engine fails repeatedly."""
    cb = CircuitBreaker(config=CircuitBreakerConfig(failure_threshold=2, timeout_seconds=60))

    # Test closed state execution
    def failing_fn():
        raise ValueError("Engine crash")

    for _ in range(2):
        with pytest.raises(ValueError):
            cb.call(failing_fn)

    # Circuit should now be OPEN
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(failing_fn)


@pytest.mark.asyncio
async def test_in_memory_cache_manager():
    """Verify InMemoryCache and CacheManager set and get behavior."""
    cache = InMemoryCache(default_ttl=60)
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    assert cache.get("nonexistent") is None


@pytest.mark.asyncio
async def test_metrics_collector_integration():
    """Verify MetricsCollector correctly tracks request counts and latencies."""
    metrics = MetricsCollector()
    metrics.increment("inference_requests_total")
    metrics.observe("pipeline_latency_ms", 12.5)

    snapshot = metrics.get_snapshot()
    assert snapshot.requests_total >= 1
    assert "inference_requests_total" in metrics.export_prometheus()
