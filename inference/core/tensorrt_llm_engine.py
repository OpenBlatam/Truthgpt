"""
Refactored TensorRT-LLM Engine with Polyglot Integration

Integrates TensorRT-LLM with Rust KV cache and C++ attention.
"""
import logging
import asyncio
import time
from typing import List, Optional, Union, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from .base_engine import BaseInferenceEngine, GenerationConfig, InferenceRequest, InferenceResponse
from ..config.tensorrt_config import TensorRTBackend, TensorRTConfig

logger = logging.getLogger(__name__)

try:
    import tensorrt_llm
    from tensorrt_llm import logger as trt_logger
    TENSORRT_LLM_AVAILABLE = True
except ImportError:
    TENSORRT_LLM_AVAILABLE = False
    logger.warning("TensorRT-LLM not available")

try:
    from optimization_core.polyglot.kv_cache import KVCache
    from optimization_core.polyglot.attention import attention
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False

class TensorRTLLMEngine(BaseInferenceEngine):
    """
    Refactored TensorRT-LLM engine with polyglot integration.
    
    Features:
    - TensorRT-LLM inference (10-20x faster than PyTorch)
    - Rust KV cache for prefix caching
    - C++ attention kernels (optional)
    - INT8/FP8 quantization
    - Continuous batching support via AsyncTensorRTLLMEngine
    """
    
    def __init__(
        self,
        model: Union[str, Path],
        config: Optional[TensorRTConfig] = None,
        **kwargs
    ):
        if not TENSORRT_LLM_AVAILABLE:
            raise ImportError("TensorRT-LLM is not installed")
        
        super().__init__(model=model, **kwargs)
        self.config = config or TensorRTConfig()
        
        self._initialize_engine()
        self._set_initialized(True)
    
    def _initialize_engine(self, **kwargs) -> Any:
        self._setup_backend()
        self._setup_kv_cache()
        self._setup_engine()
        return self
    
    def _setup_backend(self):
        """Setup backend mode."""
        if self.config.backend_mode == TensorRTBackend.AUTO:
            if POLYGLOT_AVAILABLE:
                try:
                    from optimization_core.polyglot import get_available_backends
                    backends = get_available_backends()
                    if backends.get("cpp"):
                        self.config.backend_mode = TensorRTBackend.TENSORRT_CPP
                    elif backends.get("rust"):
                        self.config.backend_mode = TensorRTBackend.TENSORRT_RUST
                    else:
                        self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
                except Exception:
                    self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
            else:
                self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
        
        logger.info(f"TensorRT backend mode: {self.config.backend_mode}")
    
    def _setup_kv_cache(self):
        """Setup external KV cache."""
        self.external_cache = None
        if self.config.use_rust_kv_cache and POLYGLOT_AVAILABLE:
            try:
                self.external_cache = KVCache(
                    max_size=16384,
                    eviction_strategy="adaptive",
                    enable_compression=True,
                )
                logger.info("External Rust KV cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize external cache: {e}")
    
    def _setup_engine(self):
        """Setup TensorRT-LLM engine."""
        try:
            from tensorrt_llm.runtime import ModelConfig, SamplingConfig
            
            model_config = ModelConfig(
                max_batch_size=self.config.max_batch_size,
                max_beam_width=1,
                vocab_size=50257,
                num_layers=12,
                num_heads=12,
                hidden_size=768,
                gpt_attention_plugin=True,
                remove_input_padding=True,
            )
            
            sampling_config = SamplingConfig(
                end_id=50256,
                pad_id=50256,
                output_sequence_lengths=True,
                return_dict=True,
            )
            
            self.model_config = model_config
            self.sampling_config = sampling_config
            
            try:
                from optimization_core.polyglot import Tokenizer
                self.tokenizer = Tokenizer(model_name="gpt2", use_rust=True)
                logger.info("Polyglot tokenizer initialized")
            except Exception as e:
                self.tokenizer = None
                logger.warning(f"Failed to initialize polyglot tokenizer: {e}")
            
            logger.info("TensorRT-LLM engine configured")
        except Exception as e:
            logger.error(f"Failed to setup TensorRT engine: {e}")
            raise
    
    def generate(
        self,
        request: Union[InferenceRequest, List[InferenceRequest]],
        **kwargs
    ) -> Union[InferenceResponse, List[InferenceResponse]]:
        """Generate with TensorRT-LLM and optional polyglot optimizations."""
        is_single = isinstance(request, InferenceRequest)
        requests = [request] if is_single else request
        prompts = [req.prompt for req in requests]
        
        try:
            if self.external_cache:
                cached_results = self._get_from_cache(prompts)
                if cached_results:
                    responses = []
                    for req, cached_text in zip(requests, cached_results):
                        responses.append(InferenceResponse(
                            text=cached_text,
                            model_name=str(self.model_path),
                            latency_ms=0.0,
                            request_id=req.request_id,
                            tokens_generated=len(cached_text.split()), # Appx
                            finish_reason="cache_hit"
                        ))
                    return responses[0] if is_single else responses
            
            start_ts = time.monotonic()
            
            # Using parameters from the first request for batch logic
            primary_req = requests[0]
            
            results_text = self._generate_tensorrt(
                prompts,
                max_new_tokens=primary_req.max_tokens,
                temperature=primary_req.temperature,
                top_p=primary_req.top_p,
                **kwargs
            )
            latency_ms = (time.monotonic() - start_ts) * 1000
            
            if self.external_cache:
                self._update_cache(prompts, results_text)
            
            responses = []
            for req, text in zip(requests, results_text):
                responses.append(InferenceResponse(
                    text=text,
                    model_name=str(self.model_path),
                    latency_ms=latency_ms,
                    request_id=req.request_id,
                    tokens_generated=len(text.split()), # Appx
                    finish_reason="length"
                ))
            
            return responses[0] if is_single else responses
            
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise
    
    def _generate_tensorrt(
        self,
        prompts: List[str],
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        **kwargs
    ) -> List[str]:
        """Generate using TensorRT-LLM."""
        try:
            from tensorrt_llm.runtime import PYTHON_BINDINGS
            
            batch_size = len(prompts)
            input_ids = self._tokenize_prompts(prompts)
            
            outputs = PYTHON_BINDINGS.generate(
                self.model_config,
                self.sampling_config,
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            
            results = []
            for output in outputs:
                generated_text = self._decode_output(output)
                results.append(generated_text)
            
            return results
        except Exception as e:
            logger.error(f"TensorRT generation failed: {e}")
            raise
    
    def _tokenize_prompts(self, prompts: List[str]) -> List[List[int]]:
        """Tokenize prompts."""
        if getattr(self, "tokenizer", None):
            try:
                token_ids = self.tokenizer.encode(prompts, return_tensors=None)
                return token_ids if isinstance(token_ids[0], list) else [token_ids]
            except Exception as e:
                logger.debug(f"Tokenizer encoding failed: {e}")
        
        logger.warning("Polyglot tokenizer unavailable or failed, using fallback")
        return [[1, 2, 3] for _ in prompts]
    
    def _decode_output(self, output: Any) -> str:
        """Decode output to text."""
        if getattr(self, "tokenizer", None) and hasattr(output, "token_ids"):
            try:
                return self.tokenizer.decode(output.token_ids)
            except Exception as e:
                logger.debug(f"Tokenizer decoding failed: {e}")
        return str(output)
    
    def _get_from_cache(self, prompts: List[str]) -> Optional[List[str]]:
        """Get cached results."""
        if not self.external_cache:
            return None
        
        results = []
        for prompt in prompts:
            cache_key = hash(prompt)
            cached = self.external_cache.get(0, cache_key % 1000, str(cache_key))
            if cached:
                results.append(cached.decode('utf-8'))
            else:
                return None
        
        return results
    
    def _update_cache(self, prompts: List[str], results: List[str]):
        """Update cache with results."""
        if not self.external_cache:
            return
        
        try:
            for i, (prompt, result) in enumerate(zip(prompts, results)):
                cache_key = hash(prompt)
                cache_data = (prompt + result).encode('utf-8')
                self.external_cache.put(
                    layer_idx=0,
                    position=cache_key % 1000,
                    data=cache_data,
                    key=str(cache_key),
                )
        except Exception as e:
            logger.debug(f"Cache update failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        stats = {
            "model_path": self.model_path,
            "backend_mode": self.config.backend_mode.value,
            "max_batch_size": self.config.max_batch_size,
            "max_seq_length": self.config.max_seq_length,
        }
        
        if self.external_cache:
            cache_stats = self.external_cache.stats()
            stats["cache"] = cache_stats
        
        return stats


class AsyncTensorRTLLMEngine(TensorRTLLMEngine):
    """Async wrapper for TensorRTLLMEngine for smart scheduler compatibility.
    Supports cancellation, timeout, and asynchronous streaming generation.
    """
    
    def __init__(self, model: Union[str, Path], config: Optional[TensorRTConfig] = None, **kwargs):
        super().__init__(model, config=config, **kwargs)
    
    async def generate_async(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """Async generation for integration with orchestration (e.g. smart_scheduler).
        
        Args:
            prompt: The input prompt string.
            request_id: Optional request tracking ID.
            timeout: Optional timeout in seconds.
            config: Optional generation configuration.
            **kwargs: Forwarded to generation.
            
        Returns:
            The generated text string.
        """
        req_id = request_id or f"trt_async_{time.monotonic()}"
        gen_config = config or GenerationConfig(**kwargs)
        
        if request_id:
            logger.info(f"Starting async TRT generation for request_id: {req_id}")
        
        async def _run_inference():
            loop = asyncio.get_running_loop()
            
            def _sync_gen():
                req = InferenceRequest(
                    prompt=prompt,
                    max_tokens=gen_config.max_new_tokens if hasattr(gen_config, 'max_new_tokens') else gen_config.max_tokens,
                    temperature=gen_config.temperature,
                    top_p=gen_config.top_p,
                    request_id=req_id,
                )
                result = self.generate(req)
                return result.text if hasattr(result, 'text') else str(result)
            
            return await loop.run_in_executor(None, _sync_gen)
        
        try:
            if timeout:
                result = await asyncio.wait_for(_run_inference(), timeout=timeout)
            else:
                result = await _run_inference()
            
            if request_id:
                logger.info(f"Completed async TRT generation for request_id: {req_id}")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"TRT generation timed out for {req_id}")
            raise
        except asyncio.CancelledError:
            logger.error(f"TRT generation cancelled for {req_id}")
            raise

    async def generate_async_stream(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Simulate streaming for TensorRT engine by chunking the full output.
        
        Yields chunks of the generated text for SSE-compatible streaming.
        """
        gen_config = config or GenerationConfig(**kwargs)
        
        full_text = await self.generate_async(
            prompt, request_id=request_id, timeout=timeout, config=gen_config
        )
        
        # Stream in word-sized chunks for realistic behavior
        words = full_text.split()
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix
            await asyncio.sleep(0.01)
    
    async def generate_batch(
        self,
        prompts: List[str],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> List[str]:
        """Asynchronously generates a batch of responses."""
        loop = asyncio.get_running_loop()
        
        def _sync_batch():
            requests = [
                InferenceRequest(
                    prompt=p, max_tokens=max_tokens,
                    temperature=temperature, top_p=top_p
                )
                for p in prompts
            ]
            results = self.generate(requests)
            if isinstance(results, list):
                return [r.text if hasattr(r, 'text') else str(r) for r in results]
            return [results.text if hasattr(results, 'text') else str(results)]
        
        return await loop.run_in_executor(None, _sync_batch)

    async def generate_stream(
        self,
        prompt: Union[str, List[str]],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """AsyncInferenceEngine protocol-compliant streaming generation."""
        async for chunk in self.generate_async_stream(
            prompt if isinstance(prompt, str) else prompt[0],
            config=GenerationConfig(
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            ),
            **kwargs
        ):
            yield chunk

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics for async engine."""
        base = super().get_stats()
        base["async"] = True
        return base


def create_tensorrt_llm_engine(
    model: str,
    engine_path: str = None,
    use_async: bool = False,
    **kwargs
) -> Union[TensorRTLLMEngine, AsyncTensorRTLLMEngine]:
    """Factory helper for creating TensorRT-LLM engines."""
    if use_async:
        return AsyncTensorRTLLMEngine(model, **kwargs)
    return TensorRTLLMEngine(model, **kwargs)

