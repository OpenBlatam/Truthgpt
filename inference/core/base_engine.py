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

    @classmethod
    def from_dict(cls, kwargs: Dict[str, Any]) -> "GenerationConfig":
        """Safely build GenerationConfig from arbitrary kwargs dict."""
        import dataclasses
        known_fields = {f.name for f in dataclasses.fields(cls) if f.name != "extra_params"}
        known = {}
        extra = {}
        for k, v in kwargs.items():
            if k in known_fields:
                known[k] = v
            else:
                extra[k] = v
        if "extra_params" in kwargs and isinstance(kwargs["extra_params"], dict):
            extra.update(kwargs["extra_params"])
        if "max_tokens" in kwargs and "max_new_tokens" not in kwargs:
            known["max_new_tokens"] = kwargs["max_tokens"]
        return cls(**known, extra_params=extra)



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

    def to_pydantic(self) -> Any:
        """Convert to pydantic InferenceRequest model."""
        from ..schemas.requests import InferenceRequest as PydanticInferenceRequest
        params = {"max_tokens": self.max_tokens, "temperature": self.temperature, "top_p": self.top_p}
        params.update(self.extra_params)
        return PydanticInferenceRequest(
            prompt=self.prompt,
            request_id=self.request_id,
            stream=self.stream,
            params=params,
            generation_kwargs=self.extra_params
        )

    @classmethod
    def from_pydantic(cls, pydantic_obj: Any) -> "InferenceRequest":
        """Create InferenceRequest dataclass from pydantic model."""
        params = getattr(pydantic_obj, "params", {}) or {}
        gen_kwargs = getattr(pydantic_obj, "generation_kwargs", {}) or {}
        if not isinstance(params, dict):
            params = {}
        if not isinstance(gen_kwargs, dict):
            gen_kwargs = {}
        merged = {**params, **gen_kwargs}
        
        max_tokens = getattr(pydantic_obj, "max_tokens", merged.get("max_tokens", merged.get("max_new_tokens", 128)))
        temperature = getattr(pydantic_obj, "temperature", merged.get("temperature", 0.7))
        top_p = getattr(pydantic_obj, "top_p", merged.get("top_p", 0.95))
        
        return cls(
            prompt=getattr(pydantic_obj, "prompt", ""),
            max_tokens=max_tokens if max_tokens is not None else 128,
            temperature=temperature if temperature is not None else 0.7,
            top_p=top_p if top_p is not None else 0.95,
            request_id=getattr(pydantic_obj, "request_id", getattr(pydantic_obj, "id", None)),
            stream=getattr(pydantic_obj, "stream", False),
            extra_params=merged
        )


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
    model_name: str = ""
    latency_ms: float = 0.0
    request_id: Optional[str] = None
    tokens_generated: Optional[int] = None
    finish_reason: Optional[str] = None

    @property
    def output(self) -> str:
        return self.text

    def to_pydantic(self) -> Any:
        """Convert to pydantic InferenceResponse model."""
        from ..schemas.requests import InferenceResponse as PydanticInferenceResponse
        return PydanticInferenceResponse(
            text=self.text,
            output=self.text,
            model=self.model_name,
            model_name=self.model_name,
            latency_ms=self.latency_ms,
            request_id=self.request_id,
            usage={"total_tokens": self.tokens_generated} if self.tokens_generated is not None else {}
        )

    @classmethod
    def from_pydantic(cls, pydantic_obj: Any) -> "InferenceResponse":
        """Create InferenceResponse dataclass from pydantic model."""
        text = getattr(pydantic_obj, "text", getattr(pydantic_obj, "output", ""))
        model_name = getattr(pydantic_obj, "model_name", getattr(pydantic_obj, "model", ""))
        latency_ms = getattr(pydantic_obj, "latency_ms", 0.0)
        request_id = getattr(pydantic_obj, "request_id", getattr(pydantic_obj, "id", None))
        usage = getattr(pydantic_obj, "usage", {}) or {}
        tokens = usage.get("total_tokens", None)
        return cls(
            text=text,
            model_name=model_name,
            latency_ms=latency_ms,
            request_id=request_id,
            tokens_generated=tokens
        )


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
        self.model = str(self.model_path)
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

    async def initialize(self, **kwargs) -> Any:
        """Async lifecycle hook to initialize the engine."""
        if not self._initialized:
            res = self._initialize_engine(**kwargs)
            self._set_initialized(True)
            return res
        return self

    async def shutdown(self) -> None:
        """Async lifecycle hook to gracefully clean up engine resources."""
        self._set_initialized(False)

    async def warmup(self, sample_prompt: str = "Warmup prompt", max_tokens: int = 1) -> bool:
        """Warming up engine caches and graph compilation."""
        try:
            self.generate(sample_prompt, max_tokens=max_tokens)
            return True
        except Exception as e:
            logger.warning(f"Engine warmup error on {self.__class__.__name__}: {e}")
            return False

    async def check_health(self) -> bool:
        """Probe engine health state."""
        return self._initialized

    def __enter__(self):
        """Sync context manager entry."""
        if not self._initialized:
            self._initialize_engine()
            self._set_initialized(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

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
    # Asynchronous Generation & Streaming
    # ------------------------------------------------------------------

    async def generate_async(
        self,
        prompt: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[InferenceResult, List[InferenceResult]]:
        """
        Asynchronously generate text from one or more prompts.

        Default implementation executes ``generate()`` in an executor.
        Subclasses may override with native async logic.
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))

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
        loop = asyncio.get_running_loop()

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
        loop = asyncio.get_running_loop()

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
