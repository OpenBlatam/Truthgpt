"""
🧪 Enhanced Inference Module Unit Tests
Tests for schema interop, FallbackEngineProxy streaming, and ExecutionPipeline handling.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from optimization_core.inference.core.base_engine import (
    InferenceRequest as DataclassRequest,
    InferenceResponse as DataclassResponse,
    BaseInferenceEngine,
)
from optimization_core.inference.schemas.requests import (
    InferenceRequest as PydanticRequest,
    InferenceResponse as PydanticResponse,
)
from optimization_core.inference.core.engine_factory import FallbackEngineProxy
from optimization_core.inference.pipelines.execution_pipeline import ExecutionPipeline


def test_dataclass_pydantic_schema_conversion():
    """Verify bidirectional conversion between dataclass and Pydantic schemas."""
    # 1. Dataclass -> Pydantic Request
    dc_req = DataclassRequest(prompt="Test dataclass prompt", max_tokens=256, temperature=0.8, request_id="req_001")
    py_req = dc_req.to_pydantic()
    assert py_req.prompt == "Test dataclass prompt"
    assert py_req.request_id == "req_001"
    assert py_req.params["max_tokens"] == 256

    # 2. Pydantic -> Dataclass Request
    dc_req_back = PydanticRequest.to_dataclass(py_req)
    assert dc_req_back.prompt == "Test dataclass prompt"
    assert dc_req_back.request_id == "req_001"
    assert dc_req_back.max_tokens == 256

    # 3. Dataclass -> Pydantic Response
    dc_res = DataclassResponse(text="Generated answer", model_name="gpt-4", latency_ms=12.5, request_id="req_001", tokens_generated=42)
    py_res = dc_res.to_pydantic()
    assert py_res.output == "Generated answer"
    assert py_res.text == "Generated answer"
    assert py_res.model == "gpt-4"
    assert py_res.latency_ms == 12.5
    assert py_res.request_id == "req_001"

    # 4. Pydantic -> Dataclass Response
    dc_res_back = PydanticResponse.to_dataclass(py_res)
    assert dc_res_back.text == "Generated answer"
    assert dc_res_back.output == "Generated answer"
    assert dc_res_back.model_name == "gpt-4"
    assert dc_res_back.latency_ms == 12.5
    assert dc_res_back.request_id == "req_001"


@pytest.mark.asyncio
async def test_fallback_engine_proxy_streaming():
    """Verify FallbackEngineProxy handles streaming generation failover when primary engine fails."""

    class FailingStreamEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, request, **kwargs):
            raise RuntimeError("Primary engine crashed!")
        async def generate_stream(self, prompt, **kwargs):
            raise RuntimeError("Primary stream crashed!")
            yield  # unreachable

    class WorkingStreamEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, request, **kwargs):
            return "Backup response"
        async def generate_stream(self, prompt, **kwargs):
            yield "Chunk 1 "
            yield "Chunk 2"

    proxy = FallbackEngineProxy([FailingStreamEngine(model="fail"), WorkingStreamEngine(model="work")])
    chunks = []
    async for chunk in proxy.generate_stream("Stream test prompt"):
        chunks.append(chunk)

    assert "".join(chunks) == "Chunk 1 Chunk 2"


@pytest.mark.asyncio
async def test_execution_pipeline_params_handling():
    """Verify ExecutionPipeline extracts params dict and passes to engine."""

    class MockParamsEngine:
        def generate(self, prompt, **kwargs):
            max_tokens = kwargs.get("max_tokens", 0)
            return f"Prompt: {prompt}, max_tokens: {max_tokens}"

    engine = MockParamsEngine()
    pipeline = ExecutionPipeline(engine=engine)

    py_req = PydanticRequest(prompt="Hello pipeline", params={"max_tokens": 100})
    result = await pipeline.execute(py_req)
    assert result == "Prompt: Hello pipeline, max_tokens: 100"


@pytest.mark.asyncio
async def test_base_engine_context_manager_and_lifecycle():
    """Verify BaseInferenceEngine async context manager and lifecycle methods."""

    class DummyEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            return self

        def generate(self, prompts, **kwargs):
            return "Sample response"

    engine = DummyEngine(model="test_model")
    assert not engine.is_initialized

    async with engine as active_engine:
        assert active_engine.is_initialized
        assert await active_engine.check_health()
        assert await active_engine.warmup()

    assert not engine.is_initialized

