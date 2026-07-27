"""
Inference Core Components

This module contains core inference components: engines and text generator.
"""

from __future__ import annotations
import importlib

__all__ = [
    'InferenceEngine',
    'TextGenerator',
    'TensorRTLLMEngine',
    'VLLMEngine',
    'AsyncVLLMEngine',
    'AsyncTensorRTLLMEngine',
    'create_inference_engine',
    'EngineType',
    'list_available_engines',
]

_LAZY_CLASSES = {
    'InferenceEngine': '.inference_engine',
    'TextGenerator': '.text_generator',
    'TensorRTLLMEngine': '.tensorrt_llm_engine',
    'VLLMEngine': '.vllm_engine',
    'AsyncVLLMEngine': '.vllm_engine',
    'AsyncTensorRTLLMEngine': '.tensorrt_llm_engine',
    'create_inference_engine': '.engine_factory',
    'EngineType': '.engine_factory',
    'list_available_engines': '.engine_factory',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for inference core components."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    if name in _LAZY_CLASSES:
        module_path = _LAZY_CLASSES[name]
        try:
            module = importlib.import_module(module_path, package=__name__)
            obj = getattr(module, name)
            _import_cache[name] = obj
            return obj
        except Exception as e:
            raise AttributeError(
                f"module '{__name__}' has no attribute '{name}'. "
                f"Failed to import: {e}"
            ) from e
            
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def list_available_core_components() -> list[str]:
    """List all available core inference components."""
    return list(_LAZY_CLASSES.keys())


def get_core_component_info(component_name: str) -> dict[str, any]:
    """Get information about a core inference component."""
    if component_name not in _LAZY_CLASSES:
        raise ValueError(f"Unknown core component: {component_name}")
    
    return {
        'name': component_name,
        'module': _LAZY_CLASSES[component_name],
        'available': component_name in _import_cache or True,
    }

