"""
Inference Engine Exceptions
============================

Custom exceptions for inference engines with detailed error information.
"""

from typing import Optional, Dict, Any, List


class OptimizationCoreException(Exception):
    """Root exception for optimization core errors with enriched contextual details."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        remediation_hint: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        import time
        self.message = message
        self.details = details or {}
        self.error_code = error_code or "ERR_OPT_CORE_GENERIC"
        self.remediation_hint = remediation_hint or "Check server logs for detailed stacktrace."
        self.timestamp = time.time()
        
        formatted_message = f"[{self.error_code}] {message}"
        if self.remediation_hint:
            formatted_message += f" | Remediation: {self.remediation_hint}"
        
        super().__init__(formatted_message)


class InferenceError(OptimizationCoreException):
    """Base exception for inference operations."""
    pass


class ModelError(OptimizationCoreException):
    """Base exception for model loading or structure errors."""
    pass


class CoreValidationError(OptimizationCoreException):
    """Base exception for validation errors."""
    pass


class ResourceError(OptimizationCoreException):
    """Base exception for out-of-memory or resource allocation errors."""
    pass


class ConfigurationError(OptimizationCoreException):
    """Base exception for invalid configuration parameters."""
    pass


class InferenceEngineError(InferenceError):
    """
    Base exception for inference engine errors.
    """

    def __init__(self, message: str, engine_type: Optional[str] = None, **kwargs: Any) -> None:
        details = kwargs.pop("details", {})
        if engine_type:
            details["engine_type"] = engine_type
        super().__init__(message, details=details, **kwargs)
        self.engine_type = engine_type


class EngineInitializationError(InferenceEngineError):
    """Raised when engine initialization fails."""
    pass


class EngineNotInitializedError(InferenceEngineError):
    """Raised when engine is not initialized."""
    pass


class GenerationError(InferenceEngineError):
    """Raised when text generation fails."""
    pass


class StreamGenerationError(GenerationError):
    """Raised when streaming token generation fails."""
    pass


class ValidationError(CoreValidationError):
    """Raised when input validation fails."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when model file is not found."""
    pass


class EngineCompilationError(InferenceEngineError):
    """Raised when engine compilation fails."""
    pass


class QuantizationError(InferenceEngineError):
    """Raised when quantization fails."""
    pass


class BatchProcessingError(InferenceEngineError):
    """Raised when batch processing fails."""
    pass


class CacheError(InferenceEngineError):
    """Raised when cache operations encounter errors."""
    pass


class KVCacheOverflowError(CacheError):
    """Raised when KV cache memory footprint exceeds configured allocation limit."""
    pass


class PolyglotBindingError(InferenceEngineError):
    """Raised when a polyglot core binding (Rust/C++/Go) execution fails."""
    pass


class OutOfMemoryEngineError(ResourceError, InferenceEngineError):
    """Raised when an out-of-memory error occurs during engine execution."""
    pass


class CircuitBreakerOpenError(InferenceEngineError):
    """Raised when a circuit breaker blocks requests to a degraded engine backend."""
    pass


class PipelineProcessingError(InferenceError):
    """Raised when prompt pre/post-processing or middleware pipeline execution fails."""
    pass



