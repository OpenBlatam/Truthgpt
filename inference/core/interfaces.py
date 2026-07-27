"""
Strict protocols and interfaces for Inference Engines.

This module defines the architectural contracts that all inference engines
(vLLM, TensorRT-LLM, Native, etc.) must adhere to.
"""
from typing import Protocol, Union, List, Optional, AsyncGenerator, Any
from pathlib import Path
from .base_engine import GenerationConfig, InferenceResult

class IInferenceEngine(Protocol):
    """
    Protocol for synchronous inference engines.
    """
    model_path: Union[str, Path]
    
    @property
    def is_initialized(self) -> bool:
        ...

    def generate(
        self,
        prompts: Union[str, List[str]],
        max_tokens: int = 64,
        temperature: float = 0.7,
        top_p: float = 0.95,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """Synchronously generate text from prompts."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Return engine statistics for metrics."""
        ...

class IAsyncInferenceEngine(IInferenceEngine, Protocol):
    """
    Protocol for asynchronous inference engines with cancellation support.
    """
    async def generate_async(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """Asynchronously generate text for a single prompt."""
        ...

    async def generate_async_stream(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Asynchronously stream generated text."""
        ...
