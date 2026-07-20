"""
polyglot_core.domain.exceptions
================================
Domain exception hierarchy — no stdlib–beyond–builtins imports.

All domain errors descend from ``DomainError``.  Framework-specific
exceptions (e.g. HTTP 400 / 500) should be mapped by the presentation
layer, not raised here.

Hierarchy::

    DomainError
    ├── ValidationError          ← invalid input / config
    │   └── ShapeError           ← tensor / array dimension mismatch
    ├── BackendUnavailableError  ← requested backend not compiled / reachable
    ├── CapacityExceededError    ← cache / batch / memory limits hit
    ├── GenerationTimeoutError   ← generation wall-clock limit exceeded
    └── QuantizationError        ← quantisation failure
"""

from __future__ import annotations

from typing import Any, Optional


class DomainError(Exception):
    """
    Base for all polyglot_core domain errors.

    Carries an optional *context* dict for structured logging.

    Example::

        raise DomainError("Something went wrong", context={"component": "cache"})
    """

    def __init__(
        self,
        message: str,
        *,
        context: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict = context or {}

    def __str__(self) -> str:
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} [{ctx_str}]"
        return self.message


class ValidationError(DomainError):
    """
    Raised when an input value or configuration is invalid.

    Example::

        raise ValidationError(
            "temperature must be in (0, 100]",
            field="temperature",
            received=0.0,
        )
    """

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        received: Any = None,
        expected: Any = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if field is not None:
            ctx["field"] = field
        if received is not None:
            ctx["received"] = received
        if expected is not None:
            ctx["expected"] = expected
        super().__init__(message, context=ctx)
        self.field = field
        self.received = received
        self.expected = expected


class ShapeError(ValidationError):
    """
    Specialised *ValidationError* for tensor / array dimension mismatches.

    Example::

        raise ShapeError(
            "query shape mismatch",
            expected_shape=(4, 512, 4096),
            actual_shape=(4, 256, 4096),
        )
    """

    def __init__(
        self,
        message: str,
        *,
        expected_shape: Any = None,
        actual_shape: Any = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if expected_shape is not None:
            ctx["expected_shape"] = expected_shape
        if actual_shape is not None:
            ctx["actual_shape"] = actual_shape
        super().__init__(message, context=ctx)
        self.expected_shape = expected_shape
        self.actual_shape = actual_shape


class BackendUnavailableError(DomainError):
    """
    Raised when the requested execution backend is not available.

    Contains the requested backend name and an optional list of
    available alternatives.

    Example::

        raise BackendUnavailableError(
            "CPP_CUDA backend requires CUDA ≥ 11.0",
            requested="cpp_cuda",
            alternatives=["rust", "python"],
        )
    """

    def __init__(
        self,
        message: str,
        *,
        requested: Optional[str] = None,
        alternatives: Optional[list] = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if requested is not None:
            ctx["requested"] = requested
        if alternatives is not None:
            ctx["alternatives"] = alternatives
        super().__init__(message, context=ctx)
        self.requested = requested
        self.alternatives = alternatives or []


class CapacityExceededError(DomainError):
    """
    Raised when a capacity limit (cache size, batch size, memory) is exceeded.

    Example::

        raise CapacityExceededError(
            "KV-cache capacity exceeded",
            limit=8192,
            current=8193,
            resource="kv_cache_entries",
        )
    """

    def __init__(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
        current: Optional[int] = None,
        resource: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if limit is not None:
            ctx["limit"] = limit
        if current is not None:
            ctx["current"] = current
        if resource is not None:
            ctx["resource"] = resource
        super().__init__(message, context=ctx)
        self.limit = limit
        self.current = current
        self.resource = resource


class GenerationTimeoutError(DomainError):
    """
    Raised when token generation exceeds the configured wall-clock timeout.

    Example::

        raise GenerationTimeoutError(
            "Generation timed out",
            timeout_ms=5000.0,
            elapsed_ms=5001.2,
            tokens_generated=37,
        )
    """

    def __init__(
        self,
        message: str,
        *,
        timeout_ms: Optional[float] = None,
        elapsed_ms: Optional[float] = None,
        tokens_generated: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if timeout_ms is not None:
            ctx["timeout_ms"] = timeout_ms
        if elapsed_ms is not None:
            ctx["elapsed_ms"] = elapsed_ms
        if tokens_generated is not None:
            ctx["tokens_generated"] = tokens_generated
        super().__init__(message, context=ctx)
        self.timeout_ms = timeout_ms
        self.elapsed_ms = elapsed_ms
        self.tokens_generated = tokens_generated


class QuantizationError(DomainError):
    """
    Raised when quantisation cannot be applied to a tensor.

    Example::

        raise QuantizationError(
            "Cannot quantise BF16 tensor to INT2",
            source_precision="bf16",
            target_precision="int2",
            reason="INT2 quantiser not loaded",
        )
    """

    def __init__(
        self,
        message: str,
        *,
        source_precision: Optional[str] = None,
        target_precision: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        ctx = dict(context or {})
        if source_precision is not None:
            ctx["source_precision"] = source_precision
        if target_precision is not None:
            ctx["target_precision"] = target_precision
        if reason is not None:
            ctx["reason"] = reason
        super().__init__(message, context=ctx)
        self.source_precision = source_precision
        self.target_precision = target_precision
        self.reason = reason
