"""
TruthGPT Optimization Core Utilities — Typed Exceptions Hierarchy
=================================================================
Defines domain-specific structured exceptions for the utils subsystem.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class UtilsError(Exception):
    """Base exception for all utility errors in optimization_core."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        base = self.message
        if self.details:
            base += f" | Details: {self.details}"
        if self.cause:
            base += f" [Caused by: {repr(self.cause)}]"
        return base


# Primary alias
UtilityError = UtilsError


class UtilityNotFoundError(UtilsError):
    """Raised when a requested utility component or module is not found."""
    pass


class UtilityConfigurationError(UtilsError):
    """Raised when an invalid configuration is supplied to a utility."""
    pass


class UtilityExecutionError(UtilsError):
    """Raised when a utility operation fails during execution."""
    pass


class HardwareError(UtilsError):
    """Raised when hardware detection, CUDA allocation, or device access fails."""
    pass


HardwareUnavailableError = HardwareError


class CUDAKernelError(HardwareError):
    """Raised when CUDA kernel execution, compilation, or tuning fails."""
    pass


class MemoryOptimizationError(UtilsError):
    """Raised during memory pooling, allocation caching, or defragmentation errors."""
    pass


class AdapterError(UtilsError):
    """Raised when an enterprise, runtime, or TruthGPT adapter fails to bridge components."""
    pass


class MonitoringError(UtilsError):
    """Raised when telemetry collection, metric logging, or alert dispatch fails."""
    pass


class RegistryError(UtilsError):
    """Raised when registering or looking up a component in UtilityRegistry fails."""
    pass


class BenchmarkError(UtilsError):
    """Raised when benchmarking a callable fails or produces non-finite stats."""
    pass


class CheckpointError(UtilsError):
    """Raised when inspecting, summarizing, or cleaning up checkpoints fails."""
    pass


class ResilienceError(UtilsError):
    """Base exception for resilience and fault-tolerance errors."""
    pass


class CircuitBreakerOpenError(ResilienceError):
    """Raised when an operation is rejected because the circuit breaker is in OPEN state."""

    def __init__(self, breaker_name: str = "default", failure_count: int = 0, cooldown_remaining: Optional[float] = None):
        details: Dict[str, Any] = {"breaker_name": breaker_name, "failure_count": failure_count}
        if cooldown_remaining is not None:
            details["cooldown_remaining_sec"] = round(cooldown_remaining, 2)
        super().__init__(f"Circuit breaker '{breaker_name}' is OPEN. Requests temporarily rejected.", details=details)


class RateLimitExceededError(ResilienceError):
    """Raised when requests exceed configured rate limiter thresholds."""

    def __init__(self, limit: int = 100, window_sec: float = 60.0, retry_after_sec: Optional[float] = None):
        details: Dict[str, Any] = {"limit": limit, "window_sec": window_sec}
        if retry_after_sec is not None:
            details["retry_after_sec"] = round(retry_after_sec, 2)
        super().__init__(f"Rate limit exceeded: {limit} requests per {window_sec}s.", details=details)


class MaxRetriesExceededError(ResilienceError):
    """Raised when an operation fails after exhausting all retry attempts."""

    def __init__(self, max_attempts: int = 3, last_exception: Optional[Exception] = None):
        super().__init__(f"Operation failed after {max_attempts} retry attempts.", details={"max_attempts": max_attempts}, cause=last_exception)


class ValidationFailureError(UtilsError):
    """Raised when schema or parameter validation fails."""
    pass


class SerializationFailureError(UtilsError):
    """Raised when serialization or deserialization of an artifact fails."""
    pass


class HealthCheckFailedError(UtilsError):
    """Raised when a utility fails its diagnostic health check."""
    pass


class TaskExecutionError(UtilsError):
    """Raised when a background or scheduled task encounters a fatal error."""
    pass


__all__ = [
    "UtilsError",
    "UtilityError",
    "UtilityNotFoundError",
    "UtilityConfigurationError",
    "UtilityExecutionError",
    "HardwareError",
    "HardwareUnavailableError",
    "CUDAKernelError",
    "MemoryOptimizationError",
    "AdapterError",
    "MonitoringError",
    "RegistryError",
    "BenchmarkError",
    "CheckpointError",
    "ResilienceError",
    "CircuitBreakerOpenError",
    "RateLimitExceededError",
    "MaxRetriesExceededError",
    "ValidationFailureError",
    "SerializationFailureError",
    "HealthCheckFailedError",
    "TaskExecutionError",
]
