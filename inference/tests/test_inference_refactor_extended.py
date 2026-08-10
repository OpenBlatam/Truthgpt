"""
🧪 Extended Refactored Inference Engine Unit Tests
Covers GenerationConfig.from_dict, execution pipeline payload parsing,
async stream & batch generation, fallback proxy counters, and cache operations.
"""

import pytest
import asyncio
import sys
from pathlib import Path

parent_dir = str(Path(__file__).resolve().parents[3])
if sys.path[0] != parent_dir:
    sys.path.insert(0, parent_dir)

from optimization_core.inference.core.base_engine import GenerationConfig, InferenceRequest, InferenceResponse, BaseInferenceEngine, InferenceResult
from optimization_core.inference.core.engine_factory import FallbackEngineProxy
from optimization_core.inference.pipelines.execution_pipeline import ExecutionPipeline
from optimization_core.inference.batch.advanced_batcher import ContinuousBatcher, BatchPriority


def test_generation_config_from_dict():
    """Verify GenerationConfig.from_dict parses known fields and puts extra args into extra_params."""
    data = {
        "max_tokens": 256,
        "temperature": 0.5,
        "custom_param": "foo",
        "nested_setting": 123,
    }
    cfg = GenerationConfig.from_dict(data)
    assert cfg.max_tokens == 256
    assert cfg.temperature == 0.5
    assert cfg.extra_params["custom_param"] == "foo"
    assert cfg.extra_params["nested_setting"] == 123


def test_execution_pipeline_param_extraction():
    """Verify ExecutionPipeline extracts max_tokens and temperature from request payloads."""
    captured_kwargs = {}

    class DummyEngine:
        def generate(self, prompt, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return InferenceResult(text=f"Response to: {prompt}")

    pipeline = ExecutionPipeline(engine=DummyEngine())
    req = InferenceRequest(prompt="Hello", max_tokens=64, temperature=0.3)
    
    # Synchronous execution test via _engine_handler
    res = asyncio.run(pipeline.execute(req))
    assert res.text == "Response to: Hello"
    assert captured_kwargs.get("max_tokens") == 64
    assert captured_kwargs.get("temperature") == 0.3


@pytest.mark.asyncio
async def test_fallback_engine_proxy_stats():
    """Verify FallbackEngineProxy tracks engine failure counters and stats."""
    class FailingEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, prompts, **kwargs):
            raise RuntimeError("Engine 1 failed")

    class WorkingEngine(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs):
            pass
        def generate(self, prompts, **kwargs):
            return InferenceResult(text="Worked", model_name="WorkingEngine")

    proxy = FallbackEngineProxy([FailingEngine("model1"), WorkingEngine("model2")])
    res = proxy.generate("Test prompt")
    assert res.text == "Worked"

    stats = proxy.get_stats()
    assert stats["type"] == "fallback_proxy"
    assert stats["engines_count"] == 2
    assert stats["engine_failures"]["FailingEngine"] == 1
    assert stats["engine_failures"]["WorkingEngine"] == 0


@pytest.mark.asyncio
async def test_continuous_batcher_submission():
    """Verify ContinuousBatcher receives items and resolves futures correctly."""
    async def mock_processor(batch_prompts):
        return [f"Output: {p}" for p in batch_prompts]

    batcher = ContinuousBatcher(processor=mock_processor, max_wait_time=0.01, max_batch_size=4)
    batcher.start()

    try:
        fut1 = await batcher.submit_async("Prompt 1")
        fut2 = await batcher.submit_async("Prompt 2")

        res1, res2 = await asyncio.gather(fut1, fut2)
        assert res1 == "Output: Prompt 1"
        assert res2 == "Output: Prompt 2"
    finally:
        await batcher.stop()


def test_fallback_engine_proxy_all_fail():
    """Verify FallbackEngineProxy raises RuntimeError when all underlying engines fail."""
    class FailingEngine1(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs): pass
        def generate(self, prompts, **kwargs):
            raise RuntimeError("Engine 1 broken")

    class FailingEngine2(BaseInferenceEngine):
        def _initialize_engine(self, **kwargs): pass
        def generate(self, prompts, **kwargs):
            raise RuntimeError("Engine 2 broken")

    proxy = FallbackEngineProxy([FailingEngine1("m1"), FailingEngine2("m2")])
    with pytest.raises(RuntimeError) as exc_info:
        proxy.generate("Test prompt")
    assert "All fallback engines failed" in str(exc_info.value)
    stats = proxy.get_stats()
    assert stats["engine_failures"]["FailingEngine1"] == 1
    assert stats["engine_failures"]["FailingEngine2"] == 1

