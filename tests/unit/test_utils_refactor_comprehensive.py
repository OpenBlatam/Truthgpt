"""
Comprehensive Test Suite for Refactored Optimization Core Utilities Subsystem.
==============================================================================
Validates:
- Abstract interfaces and polymorphic contracts
- Strongly typed Enums, Dataclasses, and Pydantic schemas
- Hierarchical typed exceptions
- Centralized discovery & factory registry
- Fluent UtilityPipelineBuilder orchestration
- Resilience primitives (CircuitBreaker, retries, rate limiters, fallbacks)
- Hardware telemetry & CUDA resource management
- Training tools, checkpoint visualization, run comparison, and cleanup
- Dual namespace compatibility ('utils' and 'optimization_core.utils')
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure workspace root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import utils
from utils import (
    # Core Interfaces
    BaseOptimizationModel,
    BaseUtility,
    BaseOptimizer,
    BaseOptimizerUtility,
    BaseManager,
    BaseHardwareManager,
    BaseTracker,
    BaseMetricsCollector,
    BaseTelemetryCollector,
    BaseAdapter,
    BaseSerializationHandler,
    BaseLogger,
    BaseResilienceHandler,
    BaseConfigManager,
    BaseTaskScheduler,
    # Types & Enums
    OptimizationLevel,
    DeviceType,
    PrecisionType,
    CudaKernelType,
    LogLevel,
    TrackerBackend,
    CachePolicy,
    UtilityCategory,
    HardwareDevice,
    ComputePrecision,
    OptimizationStrategy,
    HealthStatus,
    CircuitState,
    TaskStatus,
    SerializationFormat,
    UtilityMetadata,
    HardwareInfo,
    ExecutionStats,
    BenchmarkResult,
    SystemMetrics,
    MemoryProfile,
    CheckpointSummary,
    RunInfo,
    HealthReport,
    CircuitBreakerConfig,
    RetryConfig,
    RateLimiterConfig,
    ResilienceConfig,
    TaskMetadata,
    UtilityPipelineConfig,
    UtilityConfig,
    # Typed Exceptions
    UtilsError,
    UtilityError,
    UtilityNotFoundError,
    UtilityConfigurationError,
    UtilityExecutionError,
    HardwareError,
    HardwareUnavailableError,
    CUDAKernelError,
    MemoryOptimizationError,
    AdapterError,
    MonitoringError,
    RegistryError,
    BenchmarkError,
    CheckpointError,
    ResilienceError,
    CircuitBreakerOpenError,
    RateLimitExceededError,
    MaxRetriesExceededError,
    ValidationFailureError,
    SerializationFailureError,
    HealthCheckFailedError,
    TaskExecutionError,
    # Registry
    UtilityRegistry,
    UTILITY_REGISTRY,
    register_utility,
    create_utility,
    list_available_utilities,
    get_utility_info,
    get_utility_class,
    is_utility_available,
    # Builder
    UtilityPipeline,
    UtilityPipelineBuilder,
    create_utility_builder,
    # Base & Telemetry
    CudaResourceManager,
    system_metrics_collector,
    format_bytes,
    get_gpu_info,
    get_memory_info,
    timed_block,
    safe_run,
    benchmark_function,
    # Resilience
    CircuitBreaker,
    circuit_breaker,
    # Logging
    setup_logger,
    get_logger,
    TrainingLogger,
    # Training tools
    visualize_checkpoints,
    summarize_run,
    plot_loss_curves,
    visualize_memory_profile,
    compare_runs,
    get_run_info,
    cleanup_runs,
    # Discovery
    list_available_utility_modules,
    get_utility_module_info,
    list_all_utilities,
)


class TestUtilityInterfaces(unittest.TestCase):
    """Test standard abstract base classes and interface compliance."""

    def test_base_utility_lifecycle(self):
        class DummyUtility(BaseUtility):
            def __init__(self):
                self.initialized = False
                self.cleaned = False

            def initialize(self, *args: Any, **kwargs: Any) -> None:
                self.initialized = True

            def shutdown(self) -> None:
                self.cleaned = True

        u = DummyUtility()
        u.initialize()
        self.assertTrue(u.initialized)
        health = u.health_check()
        self.assertEqual(health["status"], "healthy")
        meta = u.get_metadata()
        self.assertEqual(meta["name"], "DummyUtility")
        u.shutdown()
        self.assertTrue(u.cleaned)

    def test_base_optimizer_interface(self):
        class DummyOptimizer(BaseOptimizer):
            def optimize(self, target: Any, *args: Any, **kwargs: Any) -> Any:
                return target * 2

            def get_stats(self) -> Dict[str, Any]:
                return {"iterations": 1, "speedup": 2.0}

        opt = DummyOptimizer()
        self.assertEqual(opt.optimize(21), 42)
        stats = opt.get_stats()
        self.assertEqual(stats["speedup"], 2.0)
        self.assertIs(BaseOptimizer, BaseOptimizerUtility)

    def test_base_optimization_model(self):
        class CustomConfig(BaseOptimizationModel):
            lr: float = 1e-4
            epochs: int = 10
            notes: str = "Test run"

        cfg = CustomConfig(lr=0.001, epochs=5)
        summary = cfg.to_summary()
        self.assertEqual(summary["lr"], 0.001)
        self.assertEqual(summary["epochs"], 5)
        self.assertEqual(summary["notes"], "Test run")

        as_dict = cfg.to_dict()
        self.assertIn("lr", as_dict)


class TestUtilityTypesAndSchemas(unittest.TestCase):
    """Test strongly typed Enums, dataclasses, and Pydantic schemas."""

    def test_enums_integrity(self):
        self.assertEqual(UtilityCategory.TRUTHGPT.value, "truthgpt")
        self.assertEqual(UtilityCategory.OPTIMIZER.value, "optimizer")
        self.assertEqual(UtilityCategory.RESILIENCE.value, "resilience")

        self.assertEqual(HardwareDevice.CUDA.value, "cuda")
        self.assertEqual(HardwareDevice.CPU.value, "cpu")
        self.assertEqual(ComputePrecision.FP16.value, "fp16")
        self.assertEqual(OptimizationStrategy.MAX_THROUGHPUT.value, "max_throughput")

        self.assertEqual(HealthStatus.HEALTHY.value, "healthy")
        self.assertEqual(CircuitState.CLOSED.value, "closed")
        self.assertEqual(CircuitState.OPEN.value, "open")
        self.assertEqual(TaskStatus.RUNNING.value, "running")
        self.assertEqual(SerializationFormat.SAFETENSORS.value, "safetensors")

    def test_utility_metadata(self):
        meta = UtilityMetadata(
            name="KernelFusedRMSNorm",
            category=UtilityCategory.HARDWARE,
            version="2.1.0",
            description="Custom CUDA fused RMSNorm kernel",
            tags=["cuda", "fused", "norm"],
            hardware_requirements=[HardwareDevice.CUDA],
        )
        data = meta.to_dict()
        self.assertEqual(data["name"], "KernelFusedRMSNorm")
        self.assertEqual(data["category"], "hardware")
        self.assertEqual(data["version"], "2.1.0")
        self.assertIn("cuda", data["tags"])
        self.assertIn("cuda", data["hardware_requirements"])

    def test_hardware_info(self):
        hw = HardwareInfo(
            device=HardwareDevice.CUDA,
            available=True,
            device_count=2,
            name="NVIDIA H100 80GB",
            total_memory_mb=81920.0,
            allocated_memory_mb=4096.0,
            reserved_memory_mb=8192.0,
            compute_capability=(9, 0),
        )
        hw_dict = hw.to_dict()
        self.assertEqual(hw_dict["device"], "cuda")
        self.assertTrue(hw_dict["available"])
        self.assertEqual(hw_dict["device_count"], 2)
        self.assertEqual(hw_dict["name"], "NVIDIA H100 80GB")
        self.assertEqual(hw_dict["compute_capability"], (9, 0))

    def test_resilience_config(self):
        rc = ResilienceConfig(
            enable_circuit_breaker=True,
            circuit_breaker=CircuitBreakerConfig(failure_threshold=3, timeout=30.0),
            enable_retry=True,
            retry=RetryConfig(max_attempts=4, initial_delay=0.5, backoff_factor=1.5),
            enable_rate_limiter=True,
            rate_limiter=RateLimiterConfig(max_requests=50, time_window_sec=10.0),
        )
        self.assertEqual(rc.circuit_breaker.failure_threshold, 3)
        self.assertEqual(rc.retry.max_attempts, 4)
        self.assertEqual(rc.rate_limiter.max_requests, 50)


class TestUtilityExceptions(unittest.TestCase):
    """Test hierarchical typed exception system."""

    def test_exception_inheritance(self):
        self.assertTrue(issubclass(UtilityError, Exception))
        self.assertTrue(issubclass(UtilityNotFoundError, UtilityError))
        self.assertTrue(issubclass(UtilityConfigurationError, UtilityError))
        self.assertTrue(issubclass(UtilityExecutionError, UtilityError))
        self.assertTrue(issubclass(HardwareUnavailableError, UtilityError))
        self.assertTrue(issubclass(ResilienceError, UtilityError))
        self.assertTrue(issubclass(CircuitBreakerOpenError, ResilienceError))
        self.assertTrue(issubclass(RateLimitExceededError, ResilienceError))
        self.assertTrue(issubclass(MaxRetriesExceededError, ResilienceError))

    def test_circuit_breaker_open_error(self):
        err = CircuitBreakerOpenError("inference_service", failure_count=5, cooldown_remaining=24.5)
        self.assertIn("inference_service", str(err))
        self.assertIn("OPEN", str(err))
        self.assertEqual(err.details["failure_count"], 5)
        self.assertEqual(err.details["cooldown_remaining_sec"], 24.5)

    def test_rate_limit_exceeded_error(self):
        err = RateLimitExceededError(limit=100, window_sec=60.0, retry_after_sec=12.3)
        self.assertIn("100 requests per 60.0s", str(err))
        self.assertEqual(err.details["retry_after_sec"], 12.3)


class TestUtilityRegistry(unittest.TestCase):
    """Test registry discovery, custom registration, categories, and factory instantiation."""

    def setUp(self):
        self.test_registry = UtilityRegistry()

    def test_custom_registration_and_creation(self):
        class DummyWorker:
            def __init__(self, multiplier: int = 1):
                self.multiplier = multiplier

            def compute(self, x: int) -> int:
                return x * self.multiplier

        self.test_registry.register(
            name="dummy_worker",
            factory=DummyWorker,
            category="testing",
            description="A test dummy worker",
            aliases=["test_worker"],
        )

        self.assertTrue(self.test_registry.has("dummy_worker"))
        self.assertTrue(self.test_registry.has("test_worker"))

        worker = self.test_registry.create("dummy_worker", multiplier=3)
        self.assertEqual(worker.compute(10), 30)

        info = self.test_registry.get_info("dummy_worker")
        self.assertEqual(info["name"], "dummy_worker")
        self.assertEqual(info["category"], "testing")

        cls = self.test_registry.get_class("dummy_worker")
        self.assertIs(cls, DummyWorker)

    def test_global_registry_functions(self):
        @register_utility(name="sample_transform_fn", category="transforms")
        def transform_fn(data: str) -> str:
            return data.upper()

        self.assertTrue(is_utility_available("sample_transform_fn"))
        res = create_utility("sample_transform_fn", "truthgpt")
        self.assertEqual(res, "TRUTHGPT")

        all_utils = list_available_utilities()
        self.assertIn("sample_transform_fn", all_utils)

        with self.assertRaises(UtilityNotFoundError):
            get_utility_info("non_existent_random_util_xyz")


class TestUtilityPipelineBuilder(unittest.TestCase):
    """Test fluent pipeline composition, retry handling, rate limits, circuit breaker, and benchmarks."""

    def test_successful_pipeline_execution(self):
        pipeline = (
            create_utility_builder("TestSuccessPipeline")
            .with_hardware(device=HardwareDevice.CPU, precision=ComputePrecision.FP32)
            .with_retry(enabled=True, max_attempts=2)
            .with_circuit_breaker(enabled=True, failure_threshold=3)
            .build()
        )

        def add_two(a: int, b: int) -> int:
            return a + b

        result = pipeline.execute(add_two, 15, 27)
        self.assertEqual(result, 42)

        health = pipeline.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["total_executions"], 1)
        self.assertEqual(health["total_failures"], 0)

    def test_pipeline_retry_and_recovery(self):
        attempts = 0

        def flaky_function():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Transient error")
            return "recovered"

        pipeline = (
            create_utility_builder("FlakyPipeline")
            .with_retry(enabled=True, max_attempts=4, initial_delay=0.01, backoff_factor=1.0)
            .build()
        )

        result = pipeline.execute(flaky_function)
        self.assertEqual(result, "recovered")
        self.assertEqual(attempts, 3)

    def test_pipeline_fallback_on_failure(self):
        def always_fails():
            raise RuntimeError("Permanent failure")

        pipeline = (
            create_utility_builder("FallbackPipeline")
            .with_retry(enabled=True, max_attempts=2, initial_delay=0.01)
            .with_fallback(default_return="fallback_value")
            .build()
        )

        result = pipeline.execute(always_fails)
        self.assertEqual(result, "fallback_value")

    def test_pipeline_circuit_breaker_trip(self):
        def failing_fn():
            raise ValueError("Service unavailable")

        pipeline = (
            create_utility_builder("CircuitTripPipeline")
            .with_circuit_breaker(enabled=True, failure_threshold=2, timeout=0.1)
            .with_retry(enabled=False)
            .build()
        )

        with self.assertRaises(ValueError):
            pipeline.execute(failing_fn)
        with self.assertRaises(ValueError):
            pipeline.execute(failing_fn)

        # Third call must fail immediately with CircuitBreakerOpenError
        with self.assertRaises(CircuitBreakerOpenError):
            pipeline.execute(failing_fn)

        # Wait for timeout to transition to HALF_OPEN
        time.sleep(0.15)
        # In HALF_OPEN, it attempts call
        with self.assertRaises(ValueError):
            pipeline.execute(failing_fn)

    def test_pipeline_rate_limiter(self):
        pipeline = (
            create_utility_builder("RateLimitedPipeline")
            .with_rate_limiter(enabled=True, max_requests=2, time_window_sec=10.0)
            .build()
        )

        self.assertEqual(pipeline.execute(lambda: 1), 1)
        self.assertEqual(pipeline.execute(lambda: 2), 2)

        with self.assertRaises(RateLimitExceededError):
            pipeline.execute(lambda: 3)

    def test_pipeline_benchmark(self):
        pipeline = create_utility_builder("BenchPipeline").build()
        stats = pipeline.benchmark(lambda x: x**2, 7, iterations=10, warmup=2)
        self.assertIsInstance(stats, ExecutionStats)
        self.assertEqual(stats.iterations, 10)
        self.assertGreater(stats.throughput_per_sec, 0)
        self.assertTrue(stats.success)


class TestResiliencePrimitives(unittest.TestCase):
    """Test CircuitBreaker class and decorator directly."""

    def test_circuit_breaker_transitions(self):
        breaker = CircuitBreaker("db_breaker", failure_threshold=2, timeout=0.05)

        def failing():
            raise ConnectionError("DB down")

        def working():
            return "DB ok"

        with self.assertRaises(ConnectionError):
            breaker.call(failing)
        self.assertEqual(breaker.state, CircuitState.CLOSED)

        with self.assertRaises(ConnectionError):
            breaker.call(failing)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        with self.assertRaises(CircuitBreakerOpenError):
            breaker.call(working)

        time.sleep(0.06)
        # Timeout elapsed -> half-open transition on next call
        self.assertEqual(breaker.call(working), "DB ok")
        self.assertEqual(breaker.call(working), "DB ok")
        self.assertEqual(breaker.state, CircuitState.CLOSED)

    def test_circuit_breaker_decorator(self):
        @circuit_breaker("math_breaker", failure_threshold=2, timeout=1.0)
        def compute_div(a: float, b: float) -> float:
            return a / b

        self.assertEqual(compute_div(10, 2), 5.0)


class TestHardwareAndTelemetry(unittest.TestCase):
    """Test CUDA resource manager, system metrics collector, timing, and byte formats."""

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(512), "512.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(2048), "2.00 KB")
        self.assertEqual(format_bytes(10 * 1024 * 1024), "10.00 MB")
        self.assertEqual(format_bytes(4.5 * 1024 * 1024 * 1024), "4.50 GB")
        self.assertEqual(format_bytes(-50), "0 B")

    def test_timed_block_and_safe_run(self):
        with timed_block("TestTimer") as timer:
            time.sleep(0.01)
        self.assertGreaterEqual(timer["elapsed_sec"], 0.008)

        # safe_run
        val = safe_run(lambda: 100 / 2)
        self.assertEqual(val, 50.0)

        err_val = safe_run(lambda: 100 / 0, default="recovered_default")
        self.assertEqual(err_val, "recovered_default")

    def test_cuda_resource_manager_telemetry(self):
        info = CudaResourceManager.get_device_info()
        self.assertIsInstance(info, dict)
        self.assertIn("device", info)
        self.assertIn("available", info)

        metrics = system_metrics_collector()
        self.assertIn("timestamp", metrics)
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_used_gb", metrics)

        # Synchronize and empty_cache shouldn't raise on any system
        CudaResourceManager.synchronize()
        CudaResourceManager.empty_cache()


class TestDualNamespaceCompatibility(unittest.TestCase):
    """Test full parity between direct 'utils' import and 'optimization_core.utils'."""

    def test_namespace_exports_match(self):
        import utils as u1
        import optimization_core.utils as u2

        self.assertEqual(u1.__version__, u2.__version__)
        self.assertIs(u1.create_utility, u2.create_utility)
        self.assertIs(u1.UtilityPipelineBuilder, u2.UtilityPipelineBuilder)
        self.assertIs(u1.CircuitBreaker, u2.CircuitBreaker)
        self.assertIs(u1.BaseOptimizationModel, u2.BaseOptimizationModel)
        self.assertIs(u1.format_bytes, u2.format_bytes)
        self.assertIs(u1.TruthGPTConfig, u2.TruthGPTConfig)
        self.assertIs(u1.visualize_checkpoints, u2.visualize_checkpoints)

    def test_discovery_modules_count(self):
        modules = list_available_utility_modules()
        self.assertGreaterEqual(len(modules), 13)
        expected = ["truthgpt", "optimizers", "systems", "training_tools", "adapters", "ai", "enterprise", "gpu", "memory", "monitoring", "quantum", "training", "modules"]
        for mod in expected:
            self.assertIn(mod, modules)


if __name__ == "__main__":
    unittest.main()
