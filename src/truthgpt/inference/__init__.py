"""
Professional inference module with batching, caching, and optimization.

This module provides organized access to inference components:
- core: Core inference components (engine, batch processor, text generator)
- middleware: Middleware components (circuit breaker, rate limiter, cache)
- monitoring: Monitoring components (metrics, observability)
- api: API server components
- utils: Utility functions
"""

from __future__ import annotations

# Direct imports for backward compatibility
from .inference_engine import InferenceEngine, BatchProcessor
from .cache_manager import CacheManager
from .text_generator import TextGenerator

# Lazy imports for organized submodules
_LAZY_IMPORTS = {
    'core': '.core',
    'middleware': '.middleware',
    'monitoring': '.monitoring',
    'api': '.api',
    'server': '.server',
    'utils': '.utils',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for inference submodules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=1)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def list_available_inference_modules() -> list[str]:
    """List all available inference submodules."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    # Core components (backward compatible)
    "InferenceEngine",
    "BatchProcessor",
    "CacheManager",
    "TextGenerator",
    # Submodules
    "core",
    "middleware",
    "monitoring",
    "api",
    "server",
    "utils",
    "list_available_inference_modules",
]
