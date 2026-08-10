"""
Refactored vLLM Engine with Polyglot Integration

Integrates vLLM with Rust KV cache and C++ attention for maximum performance.
Unified sync and async generations based on the BaseInferenceEngine architecture.
"""
import logging
import asyncio
from typing import List, Optional, Union, Dict, Any, AsyncIterator
import time

from .base_engine import BaseInferenceEngine, GenerationConfig, InferenceResult
from ..config.vllm_config import BackendMode, VLLMConfig

logger = logging.getLogger(__name__)

try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    logger.warning("vLLM not available. Install with: pip install vllm>=0.2.0")

try:
    from optimization_core.polyglot.kv_cache import KVCache
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False


class VLLMEngine(BaseInferenceEngine):
    """
    Refactored vLLM engine with unified sync and async interfaces.
    """
    
    def __init__(
        self,
        model: str,
        config: Optional[VLLMConfig] = None,
        **kwargs
    ):
        if not VLLM_AVAILABLE:
            raise ImportError("vLLM is not installed")
        
        super().__init__(model=model, **kwargs)
        self.config = config or VLLMConfig()
        
        self._async_engine = None
        self._initialize_engine()
        self._set_initialized(True)
    
    def _initialize_engine(self, **kwargs) -> Any:
        self._setup_backend()
    def _setup_engine(self):
        return self
    
    def _setup_backend(self):
        if self.config.backend_mode == BackendMode.AUTO:
            if POLYGLOT_AVAILABLE:
                try:
                    from optimization_core.polyglot import get_available_backends
                    backends = get_available_backends()
                    if backends.get("rust"):
                        self.config.backend_mode = BackendMode.VLLM_RUST
                    elif backends.get("cpp"):
                        self.config.backend_mode = BackendMode.VLLM_CPP
                    else:
                        self.config.backend_mode = BackendMode.VLLM_ONLY
                except Exception:
                    self.config.backend_mode = BackendMode.VLLM_ONLY
            else:
                self.config.backend_mode = BackendMode.VLLM_ONLY
        logger.info(f"vLLM backend mode: {self.config.backend_mode}")
    
    # _setup_kv_cache was removed because caching is handled by middleware.
    
    def _setup_engine(self):
        # We set up the async engine directly to unify architectures
        engine_args = AsyncEngineArgs(
            model=str(self.model_path),
            tensor_parallel_size=self.config.tensor_parallel_size,
            gpu_memory_utilization=self.config.gpu_memory_utilization,
            trust_remote_code=self.config.trust_remote_code,
        )
        if self.config.max_model_len:
            engine_args.max_model_len = self.config.max_model_len
        if self.config.dtype != "auto":
            engine_args.dtype = self.config.dtype
        if self.config.quantization:
            engine_args.quantization = self.config.quantization
        if self.config.enable_prefix_caching:
            engine_args.enable_prefix_caching = True
            
        try:
            self._async_engine = AsyncLLMEngine.from_engine_args(engine_args)
            logger.info(f"vLLM engine initialized: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to initialize vLLM engine: {e}")
            raise
    
    def generate(
        self,
        prompts: Union[str, List[str]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """Synchronous wrapper around async generation for compatibility."""
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(self._generate_batch_async(prompts, config, **kwargs))
            return results
        finally:
            loop.close()

    async def _generate_batch_async(self, prompts: Union[str, List[str]], config: Optional[GenerationConfig] = None, **kwargs):
        gen_config = config or GenerationConfig(**kwargs)
        single_prompt = isinstance(prompts, str)
        if single_prompt:
            prompts = [prompts]

        from vllm import SamplingParams
        sampling_params = SamplingParams(
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            max_tokens=gen_config.max_new_tokens,
            repetition_penalty=gen_config.repetition_penalty,
            stop=kwargs.get("stop", None),
        )

        request_ids = []
        for i, prompt in enumerate(prompts):
            req_id = f"gen_{time.time()}_{i}"
            await self._async_engine.add_request(req_id, prompt, sampling_params)
            request_ids.append(req_id)

        results_dict = {}
        start_ts = time.monotonic()
        
        pending = set(request_ids)
        try:
            while pending:
                async for req_output in self._async_engine.generate():
                    if req_output.finished:
                        results_dict[req_output.request_id] = req_output.outputs[0].text
                        pending.remove(req_output.request_id)
                        if not pending:
                            break

            latency_ms = (time.monotonic() - start_ts) * 1000
            
            results = [results_dict[rid] for rid in request_ids]
            inf_results = [
                InferenceResult(text=res, model_name=self.model, latency_ms=latency_ms)
                for res in results
            ]
            
            return inf_results[0] if single_prompt else inf_results
            
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise

    async def agenerate(
        self,
        prompts: Union[str, List[str]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """Async generation using native vLLM asyncio generator engine if available, or fallback."""
        gen_config = config or GenerationConfig(**kwargs)
        
        single_prompt = isinstance(prompts, str)
        if single_prompt:
            prompts = [prompts]
            
        sampling_params = SamplingParams(
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            max_tokens=gen_config.max_new_tokens,
            repetition_penalty=gen_config.repetition_penalty,
            stop=kwargs.get("stop", None),
        )
        
        import asyncio
        import uuid
        
        async_engine = AsyncLLMEngine.from_engine_args(
            AsyncEngineArgs(model=self.model)
        )
        
        results = []
        for prompt in prompts:
            request_id = str(uuid.uuid4())
            result_text = ""
            async for output in async_engine.generate(prompt, sampling_params, request_id):
                if output.finished:
                    result_text = output.outputs[0].text
            results.append(result_text)
            
        inf_results = [
            InferenceResult(text=res, model_name=self.model, latency_ms=0.0)
            for res in results
        ]
        
        return inf_results[0] if single_prompt else inf_results

    async def generate_async(self, prompt: str, request_id: Optional[str] = None, timeout: Optional[float] = None, **kwargs) -> str:
        """Native async generation avoiding nested event loops."""
        from vllm import SamplingParams
        gen_config = GenerationConfig(**kwargs)
        
        sampling_params = SamplingParams(
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            max_tokens=gen_config.max_new_tokens,
            repetition_penalty=gen_config.repetition_penalty,
        )
        
        req_id = request_id or f"gen_{time.time()}_{hash(prompt)}"
        
        async def _run():
            final_output = ""
            async for req_output in self._async_engine.generate(prompt, sampling_params, req_id):
                if req_output.finished:
                    final_output = req_output.outputs[0].text
            return final_output
            
        if timeout:
            return await asyncio.wait_for(_run(), timeout=timeout)
        return await _run()

    async def stream_async(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        from vllm import SamplingParams
        gen_config = GenerationConfig(**kwargs)
        
        sampling_params = SamplingParams(
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            max_tokens=gen_config.max_new_tokens,
            repetition_penalty=gen_config.repetition_penalty,
        )
        
        req_id = f"stream_{time.time()}_{hash(prompt)}"
        
        last_text = ""
        async for req_output in self._async_engine.generate(prompt, sampling_params, req_id):
            current_text = req_output.outputs[0].text
            if current_text != last_text:
                yield current_text[len(last_text):]
                last_text = current_text

    # _update_cache moved to middleware
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "model": str(self.model_path),
            "backend_mode": self.config.backend_mode.value,
        }
        return stats

# Export Async wrapper & VLLMInferenceEngine as aliases for backwards compatibility
AsyncVLLMEngine = VLLMEngine
VLLMInferenceEngine = VLLMEngine
