"""
Inference Engines Package.

Provides clean access to high-performance inference backends (vLLM, TensorRT-LLM, Native).
"""

from __future__ import annotations
import importlib
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'BaseInferenceEngine',
    'InferenceEngine',
    'VLLMEngine',
    'TensorRTLLMEngine',
    'create_inference_engine',
    'EngineType',
]

_LAZY_IMPORTS = {
    'BaseInferenceEngine': '..core.base_engine',
    'InferenceEngine': '..core.inference_engine',
    'VLLMEngine': '..core.vllm_engine',
    'TensorRTLLMEngine': '..core.tensorrt_llm_engine',
    'create_inference_engine': '..core.engine_factory',
    'EngineType': '..core.engine_factory',
}

_import_cache = {}


def __getattr__(name: str):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = importlib.import_module(module_path, package=__name__)
        obj = getattr(module, name)
        _import_cache[name] = obj
        return obj
    except Exception as e:
        logger.error(f"Failed to load {name} from {module_path}: {e}")
        raise AttributeError(f"module {__name__!r} cannot load {name!r}") from e
