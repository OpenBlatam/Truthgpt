"""
Inference Engine Factory.

Provides a unified factory for creating inference engines with automatic
selection based on availability and robust fallback mechanisms.
"""
import logging
from typing import Optional, Union, Dict, Any
from pathlib import Path
from optimization_core.modules.base.core_system.core.factory_base import CallableFactory, FactoryError

from .base_engine import BaseInferenceEngine
from .inference_engine import InferenceEngine, AsyncInferenceEngine
from .vllm_engine import VLLMEngine, AsyncVLLMEngine, VLLM_AVAILABLE
from .tensorrt_llm_engine import TensorRTLLMEngine, AsyncTensorRTLLMEngine, TENSORRT_LLM_AVAILABLE

logger = logging.getLogger(__name__)


class EngineType:
    """Enum-like class for engine types."""
    VLLM = "vllm"
    TENSORRT_LLM = "tensorrt_llm"
    ASYNC_VLLM = "async_vllm"
    ASYNC_TENSORRT_LLM = "async_tensorrt_llm"
    NATIVE = "native"
    ASYNC_NATIVE = "async_native"
    AUTO = "auto"
    AUTO_FALLBACK = "auto_fallback"


class FallbackEngineProxy(BaseInferenceEngine):
    """Proxy engine that attempts generation across multiple engines if one fails."""
    
    def __init__(self, engines: list[BaseInferenceEngine]):
        if not engines:
            raise ValueError("FallbackEngineProxy requires at least one engine.")
        # Store primary model path from first engine
        super().__init__(model=engines[0].model_path)
        self.engines = engines
        self._initialized = True
        
    def _initialize_engine(self, **kwargs) -> Any:
        pass
        
    def generate(self, prompts, **kwargs):
        last_err = None
        for engine in self.engines:
            try:
                return engine.generate(prompts, **kwargs)
            except Exception as e:
                logger.warning(f"Engine {engine.__class__.__name__} failed: {e}. Falling back...")
                last_err = e
        raise RuntimeError(f"All fallback engines failed. Last error: {last_err}")
        
    async def generate_async(self, prompt, **kwargs):
        last_err = None
        for engine in self.engines:
            try:
                return await engine.generate_async(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Engine {engine.__class__.__name__} async failed: {e}. Falling back...")
                last_err = e
        raise RuntimeError(f"All fallback engines failed. Last error: {last_err}")
        
    def get_stats(self) -> Dict[str, Any]:
        return {"type": "fallback_proxy", "engines_count": len(self.engines)}


class InferenceEngineFactory(CallableFactory):
    """Factory for creating inference engines."""
    
    def __init__(self):
        super().__init__(default_type=EngineType.AUTO)
        self._register_engines()
        self._prefer_gpu = True
    
    def _register_engines(self):
        """Register all engine types."""
        self.register_creator(EngineType.VLLM, self._create_vllm)
        self.register_creator(EngineType.ASYNC_VLLM, self._create_async_vllm)
        self.register_creator(EngineType.TENSORRT_LLM, self._create_tensorrt)
        self.register_creator(EngineType.ASYNC_TENSORRT_LLM, self._create_async_tensorrt)
        self.register_creator(EngineType.NATIVE, self._create_native)
        self.register_creator(EngineType.ASYNC_NATIVE, self._create_async_native)
        self.register_creator(EngineType.AUTO_FALLBACK, self._create_auto_fallback)
    
    def _check_availability(self, component_type: str) -> bool:
        """Check if engine type is available with granular logging."""
        if component_type in (EngineType.VLLM, EngineType.ASYNC_VLLM):
            is_avail = VLLM_AVAILABLE
            if not is_avail:
                logger.debug("vLLM engine requested but not available. Pip install vllm>=0.2.0.")
            return is_avail
        elif component_type in (EngineType.TENSORRT_LLM, EngineType.ASYNC_TENSORRT_LLM):
            is_avail = TENSORRT_LLM_AVAILABLE
            if not is_avail:
                logger.debug("TensorRT-LLM engine requested but not available. Install tensorrt-llm.")
            return is_avail
        return True
    
    def _create_vllm(self, model: Union[str, Path], **kwargs) -> VLLMEngine:
        if not VLLM_AVAILABLE: raise FactoryError("vLLM not available.")
        return VLLMEngine(model=str(model), **kwargs)
    
    def _create_async_vllm(self, model: Union[str, Path], **kwargs) -> AsyncVLLMEngine:
        if not VLLM_AVAILABLE: raise FactoryError("vLLM not available.")
        return AsyncVLLMEngine(model=str(model), **kwargs)
    
    def _create_tensorrt(self, model: Union[str, Path], **kwargs) -> TensorRTLLMEngine:
        if not TENSORRT_LLM_AVAILABLE: raise FactoryError("TensorRT-LLM not available.")
        return TensorRTLLMEngine(model=str(model), **kwargs)

    def _create_async_tensorrt(self, model: Union[str, Path], **kwargs) -> AsyncTensorRTLLMEngine:
        if not TENSORRT_LLM_AVAILABLE: raise FactoryError("TensorRT-LLM not available.")
        return AsyncTensorRTLLMEngine(model=str(model), **kwargs)

    def _create_native(self, model: Union[str, Path], **kwargs) -> InferenceEngine:
        return InferenceEngine(model=str(model), **kwargs)
        
    def _create_async_native(self, model: Union[str, Path], **kwargs) -> AsyncInferenceEngine:
        return AsyncInferenceEngine(model=str(model), **kwargs)
        
    def _create_auto_fallback(self, model: Union[str, Path], **kwargs) -> FallbackEngineProxy:
        engines = []
        # Try TRT -> VLLM -> Native
        if self._prefer_gpu and TENSORRT_LLM_AVAILABLE:
            engines.append(self.create(EngineType.ASYNC_TENSORRT_LLM, model=model, **kwargs))
        if VLLM_AVAILABLE:
            engines.append(self.create(EngineType.ASYNC_VLLM, model=model, **kwargs))
        engines.append(self.create(EngineType.ASYNC_NATIVE, model=model, **kwargs))
        
        return FallbackEngineProxy(engines)
    
    def select_best(self, prefer_gpu: Optional[bool] = None, async_mode: bool = False) -> str:
        prefer = prefer_gpu if prefer_gpu is not None else self._prefer_gpu
        if prefer and TENSORRT_LLM_AVAILABLE:
            return EngineType.ASYNC_TENSORRT_LLM if async_mode else EngineType.TENSORRT_LLM
        
        if VLLM_AVAILABLE:
            return EngineType.ASYNC_VLLM if async_mode else EngineType.VLLM
        
        return EngineType.ASYNC_NATIVE if async_mode else EngineType.NATIVE

    def create_with_fallback(self, engine_type: str, model: Union[str, Path], **kwargs) -> BaseInferenceEngine:
        """Create an engine with automatic fallback if the requested one fails."""
        try:
            return self.create(engine_type, model=model, **kwargs)
        except FactoryError as e:
            logger.warning(f"Failed to create primary engine '{engine_type}': {e}. Falling back to NATIVE.")
            return self._create_native(model=model, **kwargs)

_factory_instance = InferenceEngineFactory()

def create_inference_engine(
    model: Union[str, Path],
    engine_type: str = EngineType.AUTO,
    prefer_gpu: bool = True,
    use_async: bool = False,
    **kwargs
) -> BaseInferenceEngine:
    _factory_instance._prefer_gpu = prefer_gpu
    
    if engine_type == EngineType.AUTO:
        engine_type = _factory_instance.select_best(prefer_gpu=prefer_gpu, async_mode=use_async)
        logger.info(f"Auto-selected engine: {engine_type}")
    
    return _factory_instance.create_with_fallback(engine_type, model=model, **kwargs)

def list_available_engines() -> Dict[str, bool]:
    return {
        EngineType.VLLM: VLLM_AVAILABLE,
        EngineType.ASYNC_VLLM: VLLM_AVAILABLE,
        EngineType.TENSORRT_LLM: TENSORRT_LLM_AVAILABLE,
        EngineType.ASYNC_TENSORRT_LLM: TENSORRT_LLM_AVAILABLE,
        EngineType.NATIVE: True,
        EngineType.ASYNC_NATIVE: True,
        EngineType.AUTO_FALLBACK: True,
    }
