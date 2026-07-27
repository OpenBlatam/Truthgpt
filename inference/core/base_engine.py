"""
Base Inference Engine Abstract Class
=====================================

Provides the canonical interface and shared functionality for all inference engines.
All engines (vLLM, TensorRT-LLM, Native PyTorch) MUST inherit from this class
and implement the required abstract methods.

Architectural Contracts:
    - Synchronous generation: `generate()`
    - Asynchronous streaming: `generate_stream()` (async generator)
    - Asynchronous batching: `generate_batch()` (async coroutine)
    - Engine statistics: `get_stats()`

Dataclasses:
    - GenerationConfig: Sampling parameters for text generation.
    - InferenceRequest: Standardized request envelope.
    - InferenceResponse: Standardized response envelope.
    - InferenceResult: Lightweight result container (legacy compat).
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    List,
    Optional,
    Union,
    Dict,
    Any,
    AsyncGenerator,
)
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GenerationConfig:
    """
    Configuration dataclass for text generation parameters.

    Attributes:
        max_tokens: Hard cap on total tokens (prompt + generated).
        max_new_tokens: Maximum number of *new* tokens to generate.
        temperature: Sampling temperature (higher = more random).
        top_p: Nucleus sampling probability mass.
        top_k: Top-k sampling cutoff (-1 disables).
        stop: Stop sequence(s) to terminate generation.
        repetition_penalty: Penalty factor for repeated tokens.
        do_sample: Whether to use stochastic sampling.
        num_beams: Number of beams for beam search (1 = greedy/sampling).
        extra_params: Passthrough dict for engine-specific parameters.
    """
    max_tokens: int = 128
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = -1
    stop: Optional[Union[str, List[str]]] = None
    repetition_penalty: float = 1.0
    do_sample: bool = True
    num_beams: int = 1
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceRequest:
    """
    Standardized request envelope for the inference pipeline.

    Attributes:
        prompt: The input text prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        top_p: Nucleus sampling mass.
        request_id: Unique identifier for tracing.
        stream: Whether to stream the response.
        priority: Request priority (0 = normal, higher = more important).
        extra_params: Engine-specific passthrough parameters.
    """
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.95
    request_id: Optional[str] = None
    stream: bool = False
    priority: int = 0
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResponse:
    """
    Standardized response envelope from the inference pipeline.

    Attributes:
        text: The generated text output.
        model_name: Identifier of the model that produced the output.
        latency_ms: End-to-end inference latency in milliseconds.
        request_id: Echoed request identifier for tracing.
        tokens_generated: Count of tokens produced.
        finish_reason: Why generation stopped (e.g. 'stop', 'length', 'error').
    """
    text: str
    model_name: str
    latency_ms: float
    request_id: Optional[str] = None
    tokens_generated: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class InferenceResult:
    """
    Lightweight result container for backwards compatibility with engine internals.

    Attributes:
        text: Generated text.
        model_name: Model identifier.
        latency_ms: Latency measurement.
    """
    text: str
    model_name: str = ""
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Abstract Base Engine
# ---------------------------------------------------------------------------

class BaseInferenceEngine(ABC):
    """
    Abstract base class for all inference engines.

    Provides the canonical interface that the rest of the system
    (scheduler bridge, batch processor, API routers) depends on.

    Subclasses MUST implement:
        - ``_initialize_engine(**kwargs)``
        - ``generate(prompts, **kwargs)``
        - ``get_stats()``

    Subclasses SHOULD implement (for async/streaming support):
        - ``generate_stream(prompt, **kwargs)`` — async generator
        - ``generate_batch(prompts, **kwargs)`` — async coroutine
    """

    def __init__(
        self,
        model: Union[str, Path],
        **kwargs,
    ):
        """
        Initialize base inference engine.

        Args:
            model: Model name, HuggingFace ID, or filesystem path.
            **kwargs: Additional engine-specific arguments.
        """
        self.model_path = Path(model) if isinstance(model, (str, Path)) else model
        self._initialized = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _set_initialized(self, state: bool = True):
        """Mark the engine as initialized (or not)."""
        self._initialized = state

    @property
    def is_initialized(self) -> bool:
        """Whether the engine has been fully initialized."""
        return self._initialized

    @abstractmethod
    def _initialize_engine(self, **kwargs) -> Any:
        """
        Initialize the underlying engine runtime.

        Returns:
            The initialized engine object (or self).
        """
        ...

    # ------------------------------------------------------------------
    # Synchronous Generation
    # ------------------------------------------------------------------

    @abstractmethod
    def generate(
        self,
        prompts: Union[str, List[str]],
        **kwargs,
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """
        Synchronously generate text from one or more prompts.

        Args:
            prompts: A single prompt string or a list of prompts.
            **kwargs: Generation parameters (temperature, max_tokens, etc.).

        Returns:
            A single ``InferenceResult`` for a single prompt,
            or a list of ``InferenceResult`` for multiple prompts.
        """
        ...

    # ------------------------------------------------------------------
    # Asynchronous Streaming (protocol-compliant)
    # ------------------------------------------------------------------

    async def generate_stream(
        self,
        prompt: Union[str, List[str]],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously generate a token stream.

        Default implementation wraps the synchronous ``generate()`` call
        in an executor and yields the result word-by-word. Subclasses
        should override with native streaming where available.

        Yields:
            Token chunks as strings.
        """
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs,
            ),
        )
        text = result.text if hasattr(result, "text") else str(result)
        for chunk in text.split():
            yield chunk + " "
            await asyncio.sleep(0.005)

    # ------------------------------------------------------------------
    # Asynchronous Batch Generation (protocol-compliant)
    # ------------------------------------------------------------------

    async def generate_batch(
        self,
        prompts: List[str],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any,
    ) -> List[str]:
        """
        Asynchronously generate responses for a batch of prompts.

        Default implementation wraps the synchronous ``generate()`` call.
        Subclasses should override for truly parallel batch execution.

        Returns:
            List of generated text strings.
        """
        import asyncio

        loop = asyncio.get_event_loop()

        def _sync_batch():
            results = self.generate(
                prompts,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs,
            )
            if isinstance(results, list):
                return [r.text if hasattr(r, "text") else str(r) for r in results]
            return [results.text if hasattr(results, "text") else str(results)]

        return await loop.run_in_executor(None, _sync_batch)

    # ------------------------------------------------------------------
    # Statistics / Telemetry
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """
        Return engine statistics for metrics / telemetry.

        Returns:
            Dictionary of stats (model, backend, latency, cache, etc.).
        """
        return {
            "model_path": str(self.model_path),
            "initialized": self._initialized,
            "engine_class": self.__class__.__name__,
        }

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def __call__(
        self,
        prompts: Union[str, List[str]],
        **kwargs,
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """Convenience callable — delegates to ``generate()``."""
        return self.generate(prompts, **kwargs)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.model_path}, "
            f"initialized={self._initialized})"
        )
