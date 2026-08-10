"""
Professional inference module with batching, caching, and optimization.

This module provides organized access to inference components, unified backends,
and warmup utilities.
"""

from __future__ import annotations
import importlib
import logging

logger = logging.getLogger(__name__)

# Map of exported names to their module paths
_LAZY_IMPORTS = {
    # Core Components
    'BaseInferenceEngine': '.core.base_engine',
    'InferenceEngine': '.core.inference_engine',
    'AsyncInferenceEngine': '.core.inference_engine',
    'TextGenerator': '.core.text_generator',
    'TensorRTLLMEngine': '.core.tensorrt_llm_engine',
    'AsyncTensorRTLLMEngine': '.core.tensorrt_llm_engine',
    'VLLMEngine': '.core.vllm_engine',
    'AsyncVLLMEngine': '.core.vllm_engine',
    'InferenceSchedulerBridge': '.integration.scheduler_bridge',
    'create_inference_engine': '.core.engine_factory',
    'EngineType': '.core.engine_factory',
    'list_available_engines': '.core.engine_factory',
    'FallbackEngineProxy': '.core.engine_factory',
    
    # Middleware & Batching
    'BatchProcessor': '.batch.batch_scheduler',
    'CacheManager': '.middleware.cache_manager',
    'CacheInterceptor': '.middleware.cache_interceptor',
    
    # Submodules
    'core': '.core',
    'engines': '.engines',
    'interfaces': '.interfaces',
    'batch': '.batch',
    'middleware': '.middleware',
    'middlewares': '.middleware',
    'metrics': '.metrics',
    'monitoring': '.monitoring',
    'decorators': '.decorators',
    'api': '.api',
    'schemas': '.schemas',
    'config': '.config',
    'pipelines': '.pipelines',
    'schedulers': '.schedulers',
    'integration': '.integration',
    'server': '.server',
    'utils': '.utils',
}

def __getattr__(name: str):
    """Lazy import system for inference submodules and classes."""
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        
    module_path = _LAZY_IMPORTS[name]
    
    try:
        submodules = [
            'core', 'engines', 'interfaces', 'batch', 'middleware', 
            'middlewares', 'metrics', 'monitoring', 'decorators', 'api', 
            'schemas', 'config', 'pipelines', 'schedulers', 'integration',
            'server', 'utils'
        ]
        if name in submodules:
            return importlib.import_module(module_path, package=__name__)
        
        module = importlib.import_module(module_path, package=__name__)
        return getattr(module, name)
    except Exception as e:
        logger.error(f"Failed to load {name} from {module_path}: {e}")
        raise AttributeError(f"module {__name__!r} cannot load {name!r}") from e

def list_available_inference_modules() -> list[str]:
    """List all available inference components and submodules."""
    return list(_LAZY_IMPORTS.keys())

def warmup_engines(model_path: str, prefer_gpu: bool = True):
    """
    Eagerly initializes and warms up the best available inference engine in the background.
    """
    import threading
    def _warmup():
        try:
            logger.info("Starting background engine warmup...")
            factory = importlib.import_module('.core.engine_factory', package=__name__)
            # Using AUTO_FALLBACK to ensure robust warmup
            engine = factory.create_inference_engine(
                model=model_path,
                engine_type=factory.EngineType.AUTO_FALLBACK,
                prefer_gpu=prefer_gpu
            )
            # Send a dummy prompt to compile graphs or allocate caches
            engine.generate("Warmup prompt", max_new_tokens=1)
            logger.info("Engine warmup complete.")
        except Exception as e:
            logger.error(f"Engine warmup failed: {e}")
            
    t = threading.Thread(target=_warmup, daemon=True)
    t.start()
    return t

__all__ = list(_LAZY_IMPORTS.keys()) + ['list_available_inference_modules', 'warmup_engines']
