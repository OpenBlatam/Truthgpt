"""
Strict protocols and interfaces for Inference Engines.

This module re-exports the architectural contracts defined in inference.interfaces.
"""

from ..interfaces.engine_protocol import (
    IInferenceEngine,
    IAsyncInferenceEngine,
    AsyncInferenceEngine,
    EngineProtocol,
    is_engine_async,
)
from .base_engine import GenerationConfig, InferenceResult

__all__ = [
    "IInferenceEngine",
    "IAsyncInferenceEngine",
    "AsyncInferenceEngine",
    "EngineProtocol",
    "is_engine_async",
    "GenerationConfig",
    "InferenceResult",
]
