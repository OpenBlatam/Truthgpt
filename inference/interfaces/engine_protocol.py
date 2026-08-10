"""
Strict protocols for Inference Engines.
"""
from typing import Protocol, AsyncGenerator, Any, List, Optional, Dict, Union, runtime_checkable
from pathlib import Path
from abc import abstractmethod

try:
    from ..core.base_engine import GenerationConfig, InferenceResult
except ImportError:
    GenerationConfig = Any
    InferenceResult = Any


@runtime_checkable
class IInferenceEngine(Protocol):
    """
    Protocol for synchronous inference engines.
    """
    model_path: Union[str, Path]
    
    @property
    def is_initialized(self) -> bool:
        """Return initialization status of engine."""
        ...

    def generate(
        self,
        prompts: Union[str, List[str]],
        max_tokens: int = 64,
        temperature: float = 0.7,
        top_p: float = 0.95,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """Synchronously generate text from prompts."""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics for metrics."""
        ...


@runtime_checkable
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
        **kwargs: Any
    ) -> str:
        """Asynchronously generate text for a single prompt."""
        ...

    async def generate_async_stream(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Asynchronously stream generated text."""
        ...


class AsyncInferenceEngine(Protocol):
    """
    Protocol defining streaming and batching interface contracts.
    """
    @abstractmethod
    async def generate_stream(
        self, 
        prompt: Union[str, List[str]], 
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        ...
        
    @abstractmethod
    async def generate_batch(
        self,
        prompts: List[str],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> List[str]:
        ...

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        ...


# Alias EngineProtocol
EngineProtocol = IInferenceEngine


def is_engine_async(engine: Any) -> bool:
    """Check if engine implements IAsyncInferenceEngine protocol."""
    return isinstance(engine, IAsyncInferenceEngine)
