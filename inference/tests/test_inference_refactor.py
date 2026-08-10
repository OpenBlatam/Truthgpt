"""
🧪 Refactored Inference Module Unit Tests
Tests for lazy loading, schema exports, middleware resolution, and API routing.
"""

import pytest
import importlib
import sys
from pathlib import Path

# Add parent directory of optimization_core to sys.path so top-level optimization_core package resolves
parent_dir = str(Path(__file__).resolve().parents[3])
if sys.path[0] != parent_dir:
    sys.path.insert(0, parent_dir)



def test_lazy_imports_all_attributes():
    """Verify that every entry in optimization_core.inference._LAZY_IMPORTS resolves correctly."""
    import optimization_core.inference as inf
    
    available = inf.list_available_inference_modules()
    assert len(available) > 0
    
    for name in inf._LAZY_IMPORTS.keys():
        try:
            obj = getattr(inf, name)
            assert obj is not None
        except Exception as e:
            pytest.fail(f"Failed to lazy-import '{name}' from optimization_core.inference: {e}")

def test_middleware_cache_interceptor_resolution():
    """Verify CacheInterceptor resolves from optimization_core.inference.middleware."""
    from optimization_core.inference.middleware import CacheInterceptor as CI1
    from optimization_core.inference import CacheInterceptor as CI2
    
    assert CI1 is CI2

def test_schemas_module_exports():
    """Verify inference.schemas exports expected Pydantic models and configs."""
    from optimization_core.inference.schemas import (
        InferenceRequest,
        BatchInferenceRequest,
        InferenceResponse,
        BatchInferenceResponse,
        InferRequest,
        InferResponse,
        TensorRTConfig,
        VLLMConfig,
    )
    
    req = InferenceRequest(prompt="Test prompt")
    assert req.prompt == "Test prompt"
    assert req.stream is False

    infer_req = InferRequest(model="gpt-3.5", prompt="Test prompt")
    assert infer_req.prompt == "Test prompt"
    assert infer_req.model == "gpt-3.5"
    assert InferRequest is InferenceRequest
    assert InferResponse is InferenceResponse


def test_api_routers_export():
    """Verify api.routers.inference router loads successfully."""
    from optimization_core.inference.api.routers.inference import router
    assert router is not None


@pytest.mark.asyncio
async def test_execution_pipeline_and_scheduler_adapter():
    """Verify ExecutionPipeline and SmartSchedulerAdapter end-to-end execution."""
    from optimization_core.inference.pipelines.execution_pipeline import ExecutionPipeline
    from optimization_core.inference.schedulers.agent_adapter import SmartSchedulerAdapter
    from optimization_core.inference.schemas.requests import InferenceRequest

    class MockEngine:
        def generate(self, prompt, **kwargs):
            return f"Generated for: {prompt}"

    engine = MockEngine()
    pipeline = ExecutionPipeline(engine=engine, middlewares=[])
    adapter = SmartSchedulerAdapter(pipeline=pipeline)

    await adapter.start()
    try:
        req = InferenceRequest(prompt="Hello World", request_id="req_123")
        fut = await adapter.submit_request(req)
        res = await fut
        
        assert res.request_id == "req_123"
        assert res.text == "Generated for: Hello World"
        assert res.latency_ms >= 0.0
    finally:
        await adapter.stop()


def test_fallback_engine_proxy():
    """Verify FallbackEngineProxy switches to backup engine when primary fails."""
    from optimization_core.inference.core.engine_factory import FallbackEngineProxy
    from optimization_core.inference.core.base_engine import BaseInferenceEngine, InferenceRequest, InferenceResult

    class FailingEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, request, **kwargs):
            raise RuntimeError("Primary engine crashed!")

    class BackupEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, request, **kwargs):
            prompt = request.prompt if isinstance(request, InferenceRequest) else request
            return InferenceResult(text=f"Backup response for {prompt}", model_name="backup", latency_ms=1.5)

    proxy = FallbackEngineProxy([FailingEngine(model="fail"), BackupEngine(model="backup")])
    req = InferenceRequest(prompt="Test fallback")
    res = proxy.generate(req)
    assert res.text == "Backup response for Test fallback"
    assert proxy.get_stats()["type"] == "fallback_proxy"


def test_decorator_utilities():
    """Verify utils.decorators retry, cache, and validation decorators."""
    from optimization_core.inference.utils.decorators import (
        validate_inputs,
        retry_on_failure,
        cache_result,
        handle_errors,
    )

    # 1. Validation
    @validate_inputs(max_tokens=lambda x: x > 0)
    def dummy_gen(max_tokens=10):
        return f"Tokens: {max_tokens}"

    assert dummy_gen(max_tokens=5) == "Tokens: 5"
    with pytest.raises(ValueError):
        dummy_gen(max_tokens=-1)

    # 2. Retry
    attempts = 0
    @retry_on_failure(max_attempts=3, delay=0.01, backoff=1.0)
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Temporary glitch")
        return "success"

    assert flaky_func() == "success"
    assert attempts == 2

    # 3. Cache
    call_count = 0
    @cache_result(ttl=60, max_size=10)
    def cached_calc(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    assert cached_calc(5) == 10
    assert cached_calc(5) == 10
    assert call_count == 1  # Served from cache


def test_prometheus_metrics_export():
    """Verify Prometheus metrics collector records snapshot and exports metrics string."""
    from optimization_core.inference.monitoring.metrics import MetricsCollector

    collector = MetricsCollector()
    collector.increment("inference_requests_total")
    collector.set_gauge("inference_queue_depth", 3.0)
    collector.observe("inference_request_duration_ms", 45.0)

    snapshot = collector.get_snapshot()
    assert snapshot.requests_total == 1
    assert snapshot.queue_depth == 3

    exported = collector.export_prometheus()
    assert "inference_requests_total" in exported
    assert "process_uptime_seconds" in exported



