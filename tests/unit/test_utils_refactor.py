"""
Comprehensive Unit Tests for Refactored Utils Architecture
==========================================================
Validates:
1. Discovery and module introspection across all 15 subpackages
2. Thread-safe UtilityRegistry with decorator and discovery APIs
3. Declarative UtilityPipeline and UtilityPipelineBuilder
4. Foundational helpers (byte formatting, timed_block, safe_run, benchmarking)
5. Structured logging and TrainingLogger
6. Type schemas, Enums, and Pydantic BaseOptimizationModel
7. Typed exceptions hierarchy
8. Dual namespace import compatibility (utils vs optimization_core.utils)
"""

from __future__ import annotations

import os
import sys
import unittest
import time
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import utils
from utils import (
    # Submodules
    truthgpt,
    optimizers,
    systems,
    training_tools,
    adapters,
    ai,
    enterprise,
    gpu,
    memory,
    monitoring,
    quantum,
    training,
    modules,
    logging as utils_logging,
    metrics as utils_metrics,
    # Discovery
    list_available_utility_modules,
    get_utility_module_info,
    list_all_utilities,
    # Types & Enums
    OptimizationLevel,
    DeviceType,
    PrecisionType,
    CudaKernelType,
    LogLevel,
    TrackerBackend,
    CachePolicy,
    UtilityConfig,
    BenchmarkResult,
    SystemMetrics,
    MemoryProfile,
    CheckpointSummary,
    RunInfo,
    # Interfaces
    BaseOptimizationModel,
    BaseUtility,
    BaseOptimizer,
    BaseManager,
    BaseTracker,
    BaseMetricsCollector,
    BaseAdapter,
    BaseLogger,
    # Exceptions
    UtilsError,
    UtilityNotFoundError,
    UtilityConfigurationError,
    HardwareError,
    CUDAKernelError,
    MemoryOptimizationError,
    AdapterError,
    MonitoringError,
    RegistryError,
    BenchmarkError,
    CheckpointError,
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
    # Helpers
    format_bytes,
    get_gpu_info,
    get_memory_info,
    timed_block,
    safe_run,
    benchmark_function,
    CudaResourceManager,
    system_metrics_collector,
    # Logging
    setup_logger,
    get_logger,
    TrainingLogger,
    # Training tools
    visualize_checkpoints,
    summarize_run,
    compare_runs,
    get_run_info,
    cleanup_runs,
    # TruthGPT Core
    TruthGPTConfig,
    create_truthgpt_config,
    create_truthgpt_optimizer,
)


class TestUtilsModuleDiscovery(unittest.TestCase):
    """Test registry and discovery across all 15 utility subpackages."""

    def test_discovery_modules_count(self):
        modules = list_available_utility_modules()
        self.assertGreaterEqual(len(modules), 15)
        expected = [
            "truthgpt", "optimizers", "systems", "training_tools", "adapters",
            "ai", "enterprise", "gpu", "memory", "monitoring", "quantum",
            "training", "modules", "logging", "metrics"
        ]
        for name in expected:
            self.assertIn(name, modules)

    def test_get_utility_module_info(self):
        info = get_utility_module_info("gpu")
        self.assertEqual(info["name"], "gpu")
        self.assertIn("gpu", info["import_path"])

    def test_list_all_utilities_overview(self):
        all_utils = list_all_utilities()
        self.assertIn("submodules", all_utils)
        self.assertIn("types", all_utils)
        self.assertIn("interfaces", all_utils)
        self.assertIn("exceptions", all_utils)
        self.assertIn("registry", all_utils)


class TestUtilityRegistry(unittest.TestCase):
    """Test dynamic thread-safe component registration and retrieval."""

    def setUp(self):
        self.registry = UtilityRegistry()

    def test_register_and_create(self):
        class DummyWorker:
            def __init__(self, multiplier: int = 2):
                self.multiplier = multiplier
            def work(self, val: int) -> int:
                return val * self.multiplier

        self.registry.register(
            name="dummy_worker",
            factory=DummyWorker,
            category="worker",
            description="Test worker component",
        )

        self.assertTrue(self.registry.is_registered("dummy_worker"))
        self.assertIn("dummy_worker", self.registry.list_all())
        self.assertIn("worker", self.registry.list_categories())

        worker = self.registry.create("dummy_worker", multiplier=5)
        self.assertIsInstance(worker, DummyWorker)
        self.assertEqual(worker.work(10), 50)

    def test_duplicate_registration_error(self):
        def my_fn():
            return 1

        self.registry.register("my_fn", my_fn)
        with self.assertRaises(RegistryError):
            self.registry.register("my_fn", my_fn, override=False)

    def test_decorator_registration(self):
        @register_utility(name="decorated_service", category="services", override=True)
        class SampleService:
            def ping(self) -> str:
                return "pong"

        self.assertTrue(is_utility_available("decorated_service"))
        svc = create_utility("decorated_service")
        self.assertEqual(svc.ping(), "pong")


class TestUtilityPipelineBuilder(unittest.TestCase):
    """Test fluent pipeline composition and sequential execution."""

    def test_pipeline_execution(self):
        pipeline = (
            create_utility_builder("data_transform_pipeline")
            .add_step("step1_add", lambda x: x + 10)
            .add_step("step2_mul", lambda x: x * 3)
            .add_step("step3_format", lambda x: f"Result: {x}")
            .build()
        )

        output = pipeline.execute(5)
        self.assertEqual(output, "Result: 45")
        summary = pipeline.get_summary()
        self.assertEqual(summary["steps_count"], 3)
        self.assertEqual(summary["name"], "data_transform_pipeline")


class TestFoundationalHelpers(unittest.TestCase):
    """Test byte formatting, safe runner, timer context, and benchmarking."""

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(512), "512.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5), "5.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 2.5), "2.50 GB")
        self.assertEqual(format_bytes(-10), "0 B")

    def test_safe_run(self):
        def successful_op(a, b):
            return a + b
        self.assertEqual(safe_run(successful_op, 3, 7), 10)

        def failing_op():
            raise ZeroDivisionError("Failed")
        self.assertEqual(safe_run(failing_op, default="fallback"), "fallback")

    def test_timed_block(self):
        logged_msgs = []
        with timed_block("TestTimer", logger_fn=logged_msgs.append) as t:
            time.sleep(0.01)
        self.assertGreater(t["elapsed_sec"], 0.005)
        self.assertEqual(len(logged_msgs), 1)
        self.assertIn("TestTimer", logged_msgs[0])

    def test_benchmark_function(self):
        def compute_sum(n):
            return sum(range(n))

        stats = benchmark_function(compute_sum, 100, iterations=10, warmup=2)
        self.assertEqual(stats["iterations"], 10.0)
        self.assertGreater(stats["avg_ms"], 0.0)
        self.assertGreater(stats["throughput_per_sec"], 0.0)


class TestTypesAndInterfaces(unittest.TestCase):
    """Test enums, dataclasses, base schemas, and ABCs."""

    def test_enums(self):
        self.assertEqual(OptimizationLevel.ADVANCED.value, "advanced")
        self.assertEqual(DeviceType.CPU.value, "cpu")
        self.assertEqual(PrecisionType.FP16.value, "fp16")
        self.assertEqual(LogLevel.INFO.value, "INFO")
        self.assertEqual(TrackerBackend.WANDB.value, "wandb")

    def test_base_optimization_model(self):
        class SampleConfig(BaseOptimizationModel):
            batch_size: int = 64
            learning_rate: float = 0.001

        cfg = SampleConfig(batch_size=128)
        self.assertEqual(cfg.batch_size, 128)
        summary = cfg.to_summary()
        self.assertEqual(summary["batch_size"], 128)
        self.assertEqual(summary["learning_rate"], 0.001)

    def test_system_metrics_and_memory_profile(self):
        metrics = SystemMetrics(cpu_percent=25.5, memory_used_gb=4.2)
        d = metrics.to_dict()
        self.assertEqual(d["cpu_percent"], 25.5)
        self.assertEqual(d["memory_used_gb"], 4.2)

        mem = MemoryProfile(peak_gpu_memory_mb=1024.0, system_ram_used_gb=16.0)
        md = mem.to_dict()
        self.assertEqual(md["peak_gpu_memory_mb"], 1024.0)


class TestExceptionsHierarchy(unittest.TestCase):
    """Test typed exception inheritance and details payload."""

    def test_exceptions_inheritance(self):
        err = UtilityNotFoundError("Worker not found", details={"component": "gpu_worker"})
        self.assertIsInstance(err, UtilsError)
        self.assertEqual(err.details["component"], "gpu_worker")
        self.assertIn("Worker not found", str(err))

        cuda_err = CUDAKernelError("Out of memory on GPU 0")
        self.assertIsInstance(cuda_err, HardwareError)
        self.assertIsInstance(cuda_err, UtilsError)


class TestDualNamespace(unittest.TestCase):
    """Test seamless aliasing between 'utils' and 'optimization_core.utils'."""

    def test_direct_and_prefixed_modules(self):
        import utils as u1
        import optimization_core.utils as u2

        self.assertIs(u1.UtilityRegistry, u2.UtilityRegistry)
        self.assertIs(u1.BaseOptimizationModel, u2.BaseOptimizationModel)
        self.assertIs(u1.create_utility, u2.create_utility)
        self.assertIs(u1.format_bytes, u2.format_bytes)
        self.assertEqual(u1.format_bytes(2048), u2.format_bytes(2048))


if __name__ == "__main__":
    unittest.main()
