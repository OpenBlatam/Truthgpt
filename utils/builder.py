"""
Fluent Utility Pipeline Builder for Optimization Core.
======================================================
Provides declarative composition of utilities, hardware contexts,
resilience policies (circuit breaker, retries, rate limits), telemetry hooks,
and optimization routines.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

try:
    from .exceptions import (
        CircuitBreakerOpenError,
        HardwareUnavailableError,
        MaxRetriesExceededError,
        RateLimitExceededError,
        UtilityConfigurationError,
        UtilityExecutionError,
    )
    from .interfaces import BaseUtility
    from .types import (
        CircuitBreakerConfig,
        CircuitState,
        ComputePrecision,
        DeviceType,
        ExecutionStats,
        HardwareDevice,
        HardwareInfo,
        HealthReport,
        HealthStatus,
        OptimizationLevel,
        PrecisionType,
        RateLimiterConfig,
        ResilienceConfig,
        RetryConfig,
        UtilityConfig,
        UtilityPipelineConfig,
    )
except (ImportError, ValueError):
    try:
        from exceptions import (
            CircuitBreakerOpenError,
            HardwareUnavailableError,
            MaxRetriesExceededError,
            RateLimitExceededError,
            UtilityConfigurationError,
            UtilityExecutionError,
        )
        from interfaces import BaseUtility
        from types import (
            CircuitBreakerConfig,
            CircuitState,
            ComputePrecision,
            DeviceType,
            ExecutionStats,
            HardwareDevice,
            HardwareInfo,
            HealthReport,
            HealthStatus,
            OptimizationLevel,
            PrecisionType,
            RateLimiterConfig,
            ResilienceConfig,
            RetryConfig,
            UtilityConfig,
            UtilityPipelineConfig,
        )
    except (ImportError, ValueError):
        from utils.exceptions import (
            CircuitBreakerOpenError,
            HardwareUnavailableError,
            MaxRetriesExceededError,
            RateLimitExceededError,
            UtilityConfigurationError,
            UtilityExecutionError,
        )
        from utils.interfaces import BaseUtility
        from utils.types import (
            CircuitBreakerConfig,
            CircuitState,
            ComputePrecision,
            DeviceType,
            ExecutionStats,
            HardwareDevice,
            HardwareInfo,
            HealthReport,
            HealthStatus,
            OptimizationLevel,
            PrecisionType,
            RateLimiterConfig,
            ResilienceConfig,
            RetryConfig,
            UtilityConfig,
            UtilityPipelineConfig,
        )


logger = logging.getLogger(__name__)


class UtilityPipeline(BaseUtility):
    """An orchestrated utility pipeline combining resilience, telemetry, hardware checks, and benchmarking."""

    def __init__(
        self,
        config: Optional[UtilityPipelineConfig] = None,
        name: str = "default_pipeline",
        steps: Optional[List[Tuple[str, Callable[..., Any]]]] = None,
    ) -> None:
        self.config = config or UtilityPipelineConfig(pipeline_name=name)
        self.name = self.config.pipeline_name
        self.steps = steps or []
        self._execution_count = 0
        self._failure_count = 0
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._circuit_state = CircuitState.CLOSED
        self._last_state_change = time.time()
        self._request_timestamps: List[float] = []
        self._fallback_fn: Optional[Callable[..., Any]] = None
        self._default_return: Any = None
        self._has_default_return = False
        self._custom_logger_fn: Optional[Callable[[str], None]] = None
        self.results: Dict[str, Any] = {}
        self.execution_times: Dict[str, float] = {}

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize pipeline resources and verify hardware requirements."""
        self._check_hardware()

    def shutdown(self) -> None:
        """Release pipeline resources."""
        self._request_timestamps.clear()

    def health_check(self) -> Dict[str, Any]:
        """Perform a diagnostic health check on the pipeline."""
        is_healthy = self._circuit_state != CircuitState.OPEN and self._failure_count < 100
        return {
            "status": HealthStatus.HEALTHY.value if is_healthy else HealthStatus.DEGRADED.value,
            "circuit_state": self._circuit_state.value,
            "total_executions": self._execution_count,
            "total_failures": self._failure_count,
            "consecutive_failures": self._consecutive_failures,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Get pipeline metadata."""
        return {
            "name": self.config.pipeline_name,
            "device": self.config.device.value if isinstance(self.config.device, HardwareDevice) else str(self.config.device),
            "precision": self.config.precision.value if isinstance(self.config.precision, ComputePrecision) else str(self.config.precision),
            "resilience_enabled": self.config.resilience.enable_circuit_breaker or self.config.resilience.enable_retry,
            "steps_count": len(self.steps),
        }

    def _check_hardware(self) -> None:
        """Check hardware device availability."""
        if self.config.device == HardwareDevice.CUDA:
            try:
                import torch
                if not torch.cuda.is_available():
                    raise HardwareUnavailableError("cuda")
            except ImportError:
                raise HardwareUnavailableError("cuda (torch not installed)")

    def _check_circuit(self) -> None:
        """Check circuit breaker state transitions."""
        if not self.config.resilience.enable_circuit_breaker:
            return

        cb = self.config.resilience.circuit_breaker
        now = time.time()

        if self._circuit_state == CircuitState.OPEN:
            elapsed = now - self._last_state_change
            if elapsed >= cb.timeout:
                self._circuit_state = CircuitState.HALF_OPEN
                self._last_state_change = now
                self._consecutive_successes = 0
            else:
                raise CircuitBreakerOpenError(
                    self.config.pipeline_name,
                    failure_count=self._consecutive_failures,
                    cooldown_remaining=cb.timeout - elapsed,
                )

    def _check_rate_limit(self) -> None:
        """Enforce rate limiter policy."""
        if not self.config.resilience.enable_rate_limiter:
            return

        rl = self.config.resilience.rate_limiter
        now = time.time()
        cutoff = now - rl.time_window_sec

        self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]

        if len(self._request_timestamps) >= rl.max_requests:
            oldest = self._request_timestamps[0]
            retry_after = (oldest + rl.time_window_sec) - now
            raise RateLimitExceededError(rl.max_requests, rl.time_window_sec, retry_after)

        self._request_timestamps.append(now)

    def _record_success(self) -> None:
        """Record successful execution in circuit breaker state."""
        self._consecutive_failures = 0
        if self._circuit_state == CircuitState.HALF_OPEN:
            self._consecutive_successes += 1
            cb = self.config.resilience.circuit_breaker
            if self._consecutive_successes >= cb.success_threshold:
                self._circuit_state = CircuitState.CLOSED
                self._last_state_change = time.time()

    def _record_failure(self, exception: Exception) -> None:
        """Record failure in circuit breaker state."""
        self._failure_count += 1
        self._consecutive_failures += 1
        cb = self.config.resilience.circuit_breaker

        if isinstance(exception, cb.expected_exception):
            if self._circuit_state == CircuitState.HALF_OPEN or self._consecutive_failures >= cb.failure_threshold:
                self._circuit_state = CircuitState.OPEN
                self._last_state_change = time.time()

    def execute(self, func_or_input: Any = None, *args: Any, **kwargs: Any) -> Any:
        """Execute a callable with applied resilience or run pipeline steps sequentially."""
        self._execution_count += 1
        self._check_circuit()
        self._check_rate_limit()

        # If sequential steps are defined and func_or_input is not callable, run steps
        if self.steps and not callable(func_or_input):
            current_data = func_or_input
            self.results.clear()
            self.execution_times.clear()
            for step_name, fn in self.steps:
                t0 = time.perf_counter()
                try:
                    if current_data is not None:
                        current_data = fn(current_data, **kwargs)
                    else:
                        current_data = fn(**kwargs)
                    self.results[step_name] = current_data
                    self.execution_times[step_name] = time.perf_counter() - t0
                except Exception as e:
                    self._record_failure(e)
                    raise
            self._record_success()
            return current_data

        func = func_or_input if callable(func_or_input) else (lambda *a, **kw: func_or_input)

        retry_cfg = self.config.resilience.retry if self.config.resilience.enable_retry else RetryConfig(max_attempts=1)
        delay = retry_cfg.initial_delay
        last_exc: Optional[Exception] = None

        t0 = time.perf_counter()
        for attempt in range(1, retry_cfg.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - t0
                self._record_success()

                if self.config.log_telemetry and self._custom_logger_fn:
                    self._custom_logger_fn(f"[{self.config.pipeline_name}] Succeeded in {elapsed:.4f}s (attempt {attempt})")

                return result

            except Exception as e:
                last_exc = e
                self._record_failure(e)

                if attempt < retry_cfg.max_attempts and isinstance(e, retry_cfg.retry_exceptions):
                    sleep_time = delay
                    if retry_cfg.jitter:
                        sleep_time += random.uniform(0, 0.1 * delay)
                    sleep_time = min(sleep_time, retry_cfg.max_delay)
                    time.sleep(sleep_time)
                    delay *= retry_cfg.backoff_factor
                else:
                    break

        if self._fallback_fn is not None:
            try:
                return self._fallback_fn(last_exc, *args, **kwargs)
            except Exception as fallback_err:
                logger.error(f"Fallback handler raised error: {fallback_err}")

        if self._has_default_return:
            return self._default_return

        if retry_cfg.max_attempts > 1:
            raise MaxRetriesExceededError(retry_cfg.max_attempts, last_exception=last_exc) from last_exc

        raise last_exc or UtilityExecutionError(f"Pipeline execution failed for {func}")

    def __call__(self, func_or_input: Any = None, *args: Any, **kwargs: Any) -> Any:
        """Shorthand for execute."""
        return self.execute(func_or_input, *args, **kwargs)

    def benchmark(
        self,
        func: Callable[..., Any],
        *args: Any,
        iterations: int = 10,
        warmup: int = 2,
        **kwargs: Any,
    ) -> ExecutionStats:
        """Benchmark a callable over multiple iterations."""
        for _ in range(warmup):
            self.execute(func, *args, **kwargs)

        latencies: List[float] = []
        t_start = time.perf_counter()

        for _ in range(iterations):
            t0 = time.perf_counter()
            self.execute(func, *args, **kwargs)
            latencies.append(time.perf_counter() - t0)

        total_elapsed = time.perf_counter() - t_start
        avg_s = sum(latencies) / len(latencies) if latencies else 0.0

        return ExecutionStats(
            iterations=iterations,
            elapsed_sec=total_elapsed,
            avg_ms=avg_s * 1000.0,
            min_ms=min(latencies) * 1000.0 if latencies else 0.0,
            max_ms=max(latencies) * 1000.0 if latencies else 0.0,
            throughput_per_sec=1.0 / avg_s if avg_s > 0 else 0.0,
            success=True,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Return execution summary with timing metadata."""
        return {
            "name": self.name,
            "steps_count": len(self.steps),
            "step_names": [name for name, _ in self.steps],
            "execution_times_ms": {k: round(v * 1000.0, 3) for k, v in self.execution_times.items()},
            "total_time_ms": round(sum(self.execution_times.values()) * 1000.0, 3),
        }

    def reset(self) -> None:
        """Reset internal pipeline counters and circuit state."""
        self._circuit_state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._request_timestamps.clear()


class UtilityPipelineBuilder:
    """Fluent builder for constructing customized UtilityPipeline instances."""

    def __init__(self, pipeline_name: str = "CustomUtilityPipeline", name: Optional[str] = None) -> None:
        self._name = name or pipeline_name
        self._config = UtilityPipelineConfig(pipeline_name=self._name)
        self._steps: List[Tuple[str, Callable[..., Any]]] = []
        self._fallback_fn: Optional[Callable[..., Any]] = None
        self._default_return: Any = None
        self._has_default_return = False
        self._logger_fn: Optional[Callable[[str], None]] = None

    def with_name(self, name: str) -> UtilityPipelineBuilder:
        """Set pipeline identifier name."""
        self._name = name
        self._config.pipeline_name = name
        return self

    def with_config(self, config: Union[UtilityConfig, UtilityPipelineConfig]) -> UtilityPipelineBuilder:
        """Set configuration."""
        if isinstance(config, UtilityPipelineConfig):
            self._config = config
        return self

    def add_step(self, step_name_or_fn: Union[str, Callable[..., Any], Any], fn: Optional[Callable[..., Any]] = None) -> UtilityPipelineBuilder:
        """Add a procedural, transformation, or BaseUtility step."""
        if fn is None:
            # Single argument passed (e.g. util instance or function)
            callable_obj = step_name_or_fn
            name = getattr(callable_obj, "name", getattr(callable_obj, "__name__", callable_obj.__class__.__name__))
            if hasattr(callable_obj, "execute"):
                func = callable_obj.execute
            elif callable(callable_obj):
                func = callable_obj
            else:
                raise UtilityConfigurationError(f"Step '{name}' must be callable or provide execute().")
            self._steps.append((name, func))
        else:
            # Two arguments passed: step_name, fn
            name = str(step_name_or_fn)
            if not callable(fn):
                if hasattr(fn, "execute"):
                    fn = fn.execute
                else:
                    raise UtilityConfigurationError(f"Step '{name}' must be callable.")
            self._steps.append((name, fn))
        return self

    def with_optimization_level(
        self,
        level: Union[OptimizationLevel, str] = OptimizationLevel.BALANCED,
    ) -> UtilityPipelineBuilder:
        """Configure optimization aggressiveness level."""
        self._config.optimization_level = OptimizationLevel(level) if isinstance(level, str) else level
        return self

    def with_hardware(
        self,
        device: Union[HardwareDevice, DeviceType, str] = HardwareDevice.AUTO,
        precision: Union[ComputePrecision, PrecisionType, str] = ComputePrecision.FP32,
    ) -> UtilityPipelineBuilder:
        """Configure hardware accelerator device and precision."""
        self._config.device = HardwareDevice(device) if isinstance(device, str) else device
        self._config.precision = ComputePrecision(precision) if isinstance(precision, str) else precision
        return self

    def with_circuit_breaker(
        self,
        enabled: bool = True,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception,
    ) -> UtilityPipelineBuilder:
        """Configure circuit breaker resilience."""
        self._config.resilience.enable_circuit_breaker = enabled
        self._config.resilience.circuit_breaker = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
        )
        return self

    def with_retry(
        self,
        enabled: bool = True,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_exceptions: tuple = (Exception,),
    ) -> UtilityPipelineBuilder:
        """Configure exponential backoff retry mechanism."""
        self._config.resilience.enable_retry = enabled
        self._config.resilience.retry = RetryConfig(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            backoff_factor=backoff_factor,
            max_delay=max_delay,
            jitter=jitter,
            retry_exceptions=retry_exceptions,
        )
        return self

    def with_rate_limiter(
        self,
        enabled: bool = True,
        max_requests: int = 100,
        time_window_sec: float = 60.0,
    ) -> UtilityPipelineBuilder:
        """Configure request rate limiter."""
        self._config.resilience.enable_rate_limiter = enabled
        self._config.resilience.rate_limiter = RateLimiterConfig(
            max_requests=max_requests,
            time_window_sec=time_window_sec,
        )
        return self

    def with_fallback(
        self,
        default_return: Any = None,
        fallback_fn: Optional[Callable[..., Any]] = None,
    ) -> UtilityPipelineBuilder:
        """Configure fallback value or handler function on failure."""
        if default_return is not None:
            self._default_return = default_return
            self._has_default_return = True
        if fallback_fn is not None:
            self._fallback_fn = fallback_fn
        return self

    def with_telemetry(
        self,
        enabled: bool = True,
        logger_fn: Optional[Callable[[str], None]] = None,
    ) -> UtilityPipelineBuilder:
        """Enable telemetry timing and logging."""
        self._config.log_telemetry = enabled
        self._logger_fn = logger_fn
        return self

    def build(self) -> UtilityPipeline:
        """Construct the configured UtilityPipeline."""
        pipeline = UtilityPipeline(config=self._config, name=self._name, steps=self._steps)
        pipeline._fallback_fn = self._fallback_fn
        pipeline._default_return = self._default_return
        pipeline._has_default_return = self._has_default_return
        pipeline._custom_logger_fn = self._logger_fn
        pipeline.initialize()
        return pipeline


def create_utility_builder(name: str = "StandardUtilityPipeline") -> UtilityPipelineBuilder:
    """Factory helper to instantiate a new UtilityPipelineBuilder."""
    return UtilityPipelineBuilder(pipeline_name=name)


__all__ = [
    "UtilityPipeline",
    "UtilityPipelineBuilder",
    "create_utility_builder",
]
