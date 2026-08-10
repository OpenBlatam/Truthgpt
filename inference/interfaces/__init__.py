"""
Strict Interface Protocols for TruthGPT Inference.
"""

from .cache_protocol import KVCacheInterface
from .engine_protocol import (
    EngineProtocol,
    AsyncInferenceEngine,
    IInferenceEngine,
    IAsyncInferenceEngine,
    is_engine_async,
)
from .middleware_protocol import MiddlewareProtocol, NextHandler

__all__ = [
    "KVCacheInterface",
    "EngineProtocol",
    "AsyncInferenceEngine",
    "IInferenceEngine",
    "IAsyncInferenceEngine",
    "is_engine_async",
    "MiddlewareProtocol",
    "NextHandler",
]
