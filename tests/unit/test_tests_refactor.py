"""
Comprehensive Unit Tests for the Refactored TruthGPT Optimization Core Testing Framework.
"""

from __future__ import annotations

import unittest
import time
from pathlib import Path
import torch
import numpy as np

from tests.interfaces import (
    BaseTestCaseInterface,
    BaseProfilerInterface,
    BaseMemoryTrackerInterface,
    BaseAssertionInterface,
    BaseReporterInterface,
)
from tests.types import (
    TestStatus,
    TestCategory,
    TestSeverity,
    BackendType,
    BenchmarkMetric,
    MemorySnapshot,
    TestResult,
    TestSuiteResult,
    TestEnvironmentConfig,
)
from tests.exceptions import (
    TestFrameworkError,
    BackendUnavailableError,
    AssertionErrorWrapper,
    ProfilerError,
    TestTimeoutError,
)
from tests.registry import (
    TestRegistry,
    get_test_registry,
    register_test_suite,
    register_benchmark,
    register_fixture,
)
from tests.builder import (
    TestSuiteBuilder,
    BenchmarkRunnerBuilder,
    create_test_suite_builder,
    create_benchmark_builder,
)
from tests.base import BaseOptimizationCoreTestCase
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.mock_components import (
    MockOptimizer,
    MockModel,
    MockAttention,
    MockMLP,
    MockDataset,
    MockKVCache,
    MockTokenizer,
    MockTrainer,
    MockCompiler,
    MockAgent,
    MockEvaluator,
)
from tests.fixtures.test_utils import (
    TestUtils,
    PerformanceProfiler,
    MemoryTracker,
    TestAssertions,
    AdvancedTestDecorators,
)
from tests.report_generator import HTMLReportGenerator
from tests.utils.benchmark_helpers import (
    run_benchmark,
    compare_benchmarks,
    format_benchmark_result,
)


class TestFrameworkTypes(unittest.TestCase):
    """Test domain enums, dataclasses, and serialization in tests.types."""

    def test_enums(self):
        self.assertEqual(str(TestStatus.PASSED.value).lower(), "passed")
        self.assertTrue(TestStatus.PASSED.is_success())
        self.assertFalse(TestStatus.FAILED.is_success())

        self.assertEqual(str(TestCategory.UNIT.value).lower(), "unit")
        self.assertEqual(str(BackendType.PYTHON.value).lower(), "python")
        self.assertEqual(str(BackendType.RUST.value).lower(), "rust")
        self.assertEqual(str(TestSeverity.MAJOR.value).lower(), "major")

    def test_benchmark_metric_dataclass(self):
        metric = BenchmarkMetric(
            name="test_kernel",
            avg_ms=10.5,
            min_ms=9.2,
            max_ms=12.1,
            std_ms=0.8,
            p50_ms=10.4,
            p90_ms=11.5,
            p95_ms=11.8,
            p99_ms=12.0,
            throughput=95.2,
            iterations=10,
        )
        d = metric.to_dict()
        self.assertEqual(d["name"], "test_kernel")
        self.assertEqual(d["avg_ms"], 10.5)
        self.assertEqual(d["iterations"], 10)

    def test_memory_snapshot_dataclass(self):
        snap = MemorySnapshot(label="checkpoint_1", rss_mb=256.0, gpu_allocated_mb=512.0)
        d = snap.to_dict()
        self.assertEqual(d["label"], "checkpoint_1")
        self.assertEqual(d["rss_mb"], 256.0)

    def test_test_suite_result_aggregation(self):
        suite = TestSuiteResult(suite_name="UnitTests")
        r1 = TestResult(test_id="t1", name="test_one", status=TestStatus.PASSED, duration_ms=5.0)
        r2 = TestResult(test_id="t2", name="test_two", status=TestStatus.FAILED, duration_ms=15.0, error_message="Assertion failed")
        suite.add_result(r1)
        suite.add_result(r2)

        self.assertEqual(suite.total_tests, 2)
        self.assertEqual(suite.passed, 1)
        self.assertEqual(suite.failed, 1)
        self.assertEqual(suite.pass_rate, 50.0)
        self.assertFalse(suite.is_successful)


class TestFrameworkExceptions(unittest.TestCase):
    """Test typed exception hierarchy and formatting."""

    def test_base_test_framework_error(self):
        err = TestFrameworkError("Core error occurred", {"module": "compiler"})
        self.assertIn("Core error occurred", str(err))
        self.assertIn("compiler", str(err))
        self.assertEqual(err.details["module"], "compiler")

    def test_backend_unavailable_error(self):
        err = BackendUnavailableError("rust", "Cargo build not found")
        self.assertEqual(err.backend_name, "rust")
        self.assertIn("rust", str(err))
        self.assertIn("Cargo build not found", str(err))

    def test_test_timeout_error(self):
        err = TestTimeoutError("slow_test", 5.0)
        self.assertEqual(err.test_name, "slow_test")
        self.assertEqual(err.timeout_seconds, 5.0)
        self.assertIn("5.0s", str(err))


class TestFrameworkRegistry(unittest.TestCase):
    """Test centralized TestRegistry and registration decorators."""

    def setUp(self):
        self.registry = TestRegistry()

    def test_register_and_get_suite(self):
        class SampleSuite(unittest.TestCase):
            def test_dummy(self):
                pass

        self.registry.register_suite(
            name="SampleSuite",
            suite_cls_or_factory=SampleSuite,
            category=TestCategory.UNIT,
            required_backends=[BackendType.PYTHON],
            description="Sample unit test suite",
            tags=["fast", "core"],
        )

        suite_meta = self.registry.get_suite("SampleSuite")
        self.assertEqual(suite_meta["name"], "SampleSuite")
        self.assertEqual(suite_meta["category"], TestCategory.UNIT)
        self.assertIn("fast", suite_meta["tags"])

        suites_list = self.registry.list_suites(category=TestCategory.UNIT, tag="fast")
        self.assertIn("SampleSuite", suites_list)

    def test_register_and_get_benchmark(self):
        def dummy_bench():
            return 42

        self.registry.register_benchmark("dummy_benchmark", dummy_bench)
        bench_meta = self.registry.get_benchmark("dummy_benchmark")
        self.assertEqual(bench_meta["name"], "dummy_benchmark")
        self.assertEqual(bench_meta["fn"](), 42)

    def test_global_decorators(self):
        @register_test_suite(name="DecoratedSuite", category=TestCategory.SMOKE)
        class DecoratedSuite(unittest.TestCase):
            pass

        @register_benchmark(name="decorated_bench")
        def dec_bench():
            return 100

        @register_fixture(name="decorated_fix")
        def dec_fix():
            return {"key": "value"}

        g_reg = get_test_registry()
        self.assertIn("DecoratedSuite", g_reg.list_suites(category=TestCategory.SMOKE))
        self.assertIn("decorated_bench", g_reg.list_benchmarks())
        self.assertIn("decorated_fix", g_reg.list_fixtures())


class TestFrameworkBuilders(unittest.TestCase):
    """Test fluent TestSuiteBuilder and BenchmarkRunnerBuilder."""

    def test_test_suite_builder(self):
        class InnerTest(unittest.TestCase):
            def test_pass(self):
                self.assertEqual(1 + 1, 2)

        builder = (
            create_test_suite_builder("CustomSuite")
            .with_category(TestCategory.UNIT)
            .add_test_case(InnerTest)
        )
        suite = builder.build()
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(suite.countTestCases(), 1)

        result = builder.run()
        self.assertIsInstance(result, TestSuiteResult)
        self.assertEqual(result.total_tests, 1)
        self.assertEqual(result.passed, 1)
        self.assertTrue(result.is_successful)

    def test_benchmark_runner_builder(self):
        def sample_workload():
            return sum(i * i for i in range(100))

        builder = (
            create_benchmark_builder("LoopBenchmark")
            .with_target(sample_workload)
            .warmup(2)
            .iterations(5)
        )
        metric = builder.execute()
        self.assertEqual(metric.name, "LoopBenchmark")
        self.assertGreater(metric.avg_ms, 0.0)
        self.assertEqual(metric.iterations, 5)
        self.assertEqual(metric.warmup, 2)


class TestMockComponents(unittest.TestCase):
    """Verify all mock components in tests.fixtures.mock_components."""

    def test_mock_model_forward(self):
        model = MockModel(input_size=128, hidden_size=256, output_size=128)
        x = torch.randn(2, 128)
        out = model(x)
        self.assertEqual(out.shape, (2, 128))
        stats = model.get_model_stats()
        self.assertEqual(stats["forward_count"], 1)

    def test_mock_optimizer_step(self):
        opt = MockOptimizer(learning_rate=0.01)
        loss = torch.tensor(0.5)
        res = opt.step(loss)
        self.assertTrue(res["optimized"])
        self.assertEqual(opt.step_count, 1)

    def test_mock_attention(self):
        attn = MockAttention(d_model=128, n_heads=4)
        q = torch.randn(2, 16, 128)
        k = torch.randn(2, 16, 128)
        v = torch.randn(2, 16, 128)
        out, weights = attn(q, k, v)
        self.assertEqual(out.shape, (2, 16, 128))
        self.assertEqual(weights.shape, (2, 4, 16, 16))

    def test_mock_kv_cache(self):
        cache = MockKVCache(max_size=5)
        t = torch.randn(4, 4)
        cache.put("k1", t)
        self.assertIsNotNone(cache.get("k1"))
        self.assertIsNone(cache.get("k2"))
        stats = cache.get_stats()
        self.assertEqual(stats["hit_count"], 1)
        self.assertEqual(stats["miss_count"], 1)

    def test_mock_tokenizer(self):
        tok = MockTokenizer(vocab_size=500)
        tokens = tok.encode("hello world optimization")
        self.assertEqual(len(tokens), 3)
        res = tok(["hello world", "optimization core"])
        self.assertIn("input_ids", res)
        self.assertEqual(res["input_ids"].shape[0], 2)

    def test_mock_trainer(self):
        trainer = MockTrainer()
        res = trainer.train(num_epochs=2)
        self.assertEqual(res["epochs"], 2)
        self.assertTrue(trainer.is_trained)

    def test_mock_agent_and_evaluator(self):
        agent = MockAgent(name="OptAgent")
        act = agent.act({"loss": 0.2})
        self.assertEqual(act["action"], "optimize")

        evaluator = MockEvaluator()
        metrics = evaluator.evaluate(MockModel(), MockDataset(size=10))
        self.assertIn("accuracy", metrics)
        self.assertGreater(metrics["accuracy"], 0.9)


class TestProfilersAndTrackers(unittest.TestCase):
    """Verify PerformanceProfiler and MemoryTracker."""

    def test_performance_profiler(self):
        profiler = PerformanceProfiler()
        profiler.start_profile("matrix_mult")
        time.sleep(0.01)
        res = profiler.end_profile("matrix_mult")
        self.assertEqual(res["name"], "matrix_mult")
        self.assertGreater(res["execution_time_ms"], 5.0)

        summary = profiler.get_profile_summary()
        self.assertEqual(summary["total_profiles"], 1)
        profiler.reset()
        self.assertEqual(profiler.get_profile_summary()["total_profiles"], 0)

    def test_memory_tracker(self):
        tracker = MemoryTracker()
        s1 = tracker.take_snapshot("start")
        self.assertGreater(s1["rss_mb"], 0.0)
        s2 = tracker.take_snapshot("end")
        summary = tracker.get_memory_summary()
        self.assertEqual(summary["snapshots_taken"], 2)
        self.assertFalse(tracker.detect_leak(threshold_mb=10000.0))

    def test_advanced_decorators(self):
        attempts = [0]

        @AdvancedTestDecorators.retry(max_attempts=3, delay=0.01)
        def flaky_fn():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("Temporary glitch")
            return "SUCCESS"

        self.assertEqual(flaky_fn(), "SUCCESS")
        self.assertEqual(attempts[0], 2)


class TestAssertionsAndBenchmarkHelpers(unittest.TestCase):
    """Verify domain assertion helpers and benchmark statistics."""

    def test_test_assertions(self):
        assertions = TestAssertions()
        t1 = torch.tensor([1.0, 2.0, 3.0])
        t2 = torch.tensor([1.00001, 2.00001, 3.00001])
        assertions.assert_tensor_close(t1, t2, rtol=1e-3, atol=1e-3)
        assertions.assert_performance_improvement(100.0, 50.0, min_improvement=1.5)
        assertions.assert_memory_bounded(256.0, 512.0)

    def test_benchmark_helpers(self):
        def workload(n=1000):
            return sum(range(n))

        res = run_benchmark(workload, num_runs=5, warmup_runs=2, name="sum_workload")
        self.assertEqual(res.name, "sum_workload")
        self.assertEqual(res.num_runs, 5)
        self.assertGreater(res.p50_ms, 0.0)
        self.assertGreater(res.p95_ms, 0.0)

        card = format_benchmark_result(res)
        self.assertIn("Benchmark: sum_workload", card)

        compared = compare_benchmarks({"sum": res}, baseline="sum")
        self.assertIn("sum", compared)
        self.assertEqual(compared["sum"]["speedup_vs_baseline"], 1.0)


class TestReportGenerator(unittest.TestCase):
    """Verify HTML, Markdown, and JSON report generator."""

    def test_report_generation(self):
        gen = HTMLReportGenerator()
        suite = TestSuiteResult(suite_name="DemoSuite")
        suite.add_result(TestResult(test_id="t1", name="test_one", status=TestStatus.PASSED, duration_ms=2.5))
        suite.add_result(TestResult(test_id="t2", name="test_two", status=TestStatus.FAILED, duration_ms=5.0))

        html = gen.generate_html(suite.to_dict())
        self.assertIn("DemoSuite", html)

        md = gen.generate_markdown_report(suite)
        self.assertIn("# 🧪 Test Execution Report — DemoSuite", md)
        self.assertIn("test_one", md)

        summary_line = gen.format_summary(suite.to_dict())
        self.assertIn("Tests: 2 total", summary_line)


class TestBaseOptimizationCoreTestCaseUsage(BaseOptimizationCoreTestCase):
    """Verify BaseOptimizationCoreTestCase functionality."""

    def test_temp_dir_lifecycle(self):
        self.assertTrue(self.temp_dir.exists())
        temp_file = self.temp_dir / "sample.txt"
        temp_file.write_text("hello world", encoding="utf-8")
        self.assertTrue(temp_file.exists())

    def test_mock_creation_and_assertions(self):
        model = self.create_mock_engine()
        self.assertIsNotNone(model)
        proc = self.create_mock_processor()
        self.assertIsNotNone(proc)

        bench_res = self.run_benchmark(lambda: 2 + 2, num_runs=3, warmup_runs=1)
        self.assertIn("avg_ms", bench_res)


if __name__ == "__main__":
    unittest.main()
