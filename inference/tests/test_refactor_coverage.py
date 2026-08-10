"""
🧪 Refactor Coverage Tests
Additional unit tests targeting refactored components in optimization_core/inference.
"""

import pytest
import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from optimization_core.inference.core.base_engine import (
    BaseInferenceEngine,
    InferenceRequest as DataclassRequest,
    InferenceResponse as DataclassResponse,
    InferenceResult,
)
from optimization_core.inference.core.engine_factory import FallbackEngineProxy
from optimization_core.inference.pipelines.execution_pipeline import ExecutionPipeline
from optimization_core.inference.schemas.requests import InferenceRequest, InferenceResponse


class MockDummyEngine(BaseInferenceEngine):
    def __init__(self, model="dummy", **kwargs):
        super().__init__(model=model, **kwargs)
        self.initialized_calls = 0
        self.shutdown_calls = 0

    def _initialize_engine(self, **kwargs):
        self.initialized_calls += 1

    async def initialize(self, **kwargs):
        await super().initialize(**kwargs)
        return self

    async def shutdown(self) -> None:
        await super().shutdown()
        self.shutdown_calls += 1

    def generate(self, prompts, **kwargs):
        if isinstance(prompts, list):
            return [InferenceResult(text=f"Dummy: {p}", model_name=self.model) for p in prompts]
        return InferenceResult(text=f"Dummy: {prompts}", model_name=self.model)


@pytest.mark.asyncio
async def test_fallback_engine_proxy_lifecycle():
    """Verify FallbackEngineProxy delegates lifecycle hooks to all underlying engines."""
    eng1 = MockDummyEngine(model="m1")
    eng2 = MockDummyEngine(model="m2")
    proxy = FallbackEngineProxy([eng1, eng2])

    # Uninitialized engines return health False
    assert await proxy.check_health() is False

    # After initialize, health returns True
    await proxy.initialize()
    assert await proxy.check_health() is True
    assert eng1.initialized_calls == 1
    assert eng2.initialized_calls == 1

    await proxy.shutdown()
    assert eng1.shutdown_calls == 1
    assert eng2.shutdown_calls == 1
    assert proxy.is_initialized is False


@pytest.mark.asyncio
async def test_execution_pipeline_payload_variants():
    """Verify ExecutionPipeline processes pydantic request, dataclass request, dict, and str."""
    engine = MockDummyEngine(model="test_model")
    pipeline = ExecutionPipeline(engine=engine, middlewares=[])

    # 1. Pydantic request
    req_pydantic = InferenceRequest(prompt="Hello Pydantic")
    res1 = await pipeline.execute(req_pydantic)
    assert "Hello Pydantic" in (res1.text if hasattr(res1, "text") else str(res1))

    # 2. Dataclass request
    req_dataclass = DataclassRequest(prompt="Hello Dataclass")
    res2 = await pipeline.execute(req_dataclass)
    assert "Hello Dataclass" in (res2.text if hasattr(res2, "text") else str(res2))

    # 3. Dict
    req_dict = {"prompt": "Hello Dict"}
    res3 = await pipeline.execute(req_dict)
    assert "Hello Dict" in (res3.text if hasattr(res3, "text") else str(res3))

    # 4. Plain str
    res4 = await pipeline.execute("Hello String")
    assert "Hello String" in (res4.text if hasattr(res4, "text") else str(res4))


def test_schema_bidirectional_conversion_fidelity():
    """Verify complete schema conversion fidelity between Pydantic and Dataclasses."""
    p_req = InferenceRequest(
        prompt="Test Prompt",
        request_id="req_999",
        stream=True,
        params={"temperature": 0.5, "max_tokens": 256, "custom_kw": "value"},
    )
    d_req = p_req.to_dataclass()
    assert d_req.prompt == "Test Prompt"
    assert d_req.request_id == "req_999"
    assert d_req.stream is True
    assert d_req.temperature == 0.5
    assert d_req.max_tokens == 256

    reconverted_p_req = InferenceRequest.from_dataclass(d_req)
    assert reconverted_p_req.prompt == p_req.prompt
    assert reconverted_p_req.request_id == p_req.request_id
    assert reconverted_p_req.stream == p_req.stream

    d_res = DataclassResponse(
        text="Sample output text",
        model_name="test_model",
        latency_ms=12.34,
        request_id="req_999",
        tokens_generated=42,
    )
    p_res = d_res.to_pydantic()
    assert p_res.text == "Sample output text"
    assert p_res.model == "test_model"
    assert p_res.latency_ms == 12.34
    assert p_res.usage.get("total_tokens") == 42
