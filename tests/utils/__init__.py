"""
Testing Utilities and Helper Subsystems for TruthGPT Optimization Core.
"""

from __future__ import annotations

from .test_base import (
    BasePolyglotTest,
    BaseBenchmarkTest,
    BaseIntegrationTest,
    BasePerformanceTest,
)
from .benchmark_helpers import (
    BenchmarkResult,
    run_benchmark,
    compare_benchmarks,
    format_benchmark_result,
    benchmark_backends,
)
from .test_helpers import (
    create_temp_directory,
    cleanup_temp_directory,
    create_test_config,
    create_mock_processor,
    create_mock_engine,
    create_test_data_file,
    load_test_data,
    assert_dict_contains,
    retry_on_failure,
    skip_if_backend_unavailable,
    measure_time,
)
from .test_fixtures import (
    MockInferenceEngine,
    MockDataProcessor,
    TestConfig,
    TestDataGenerator,
)
from .test_assertions import (
    assert_engine_works,
    assert_processor_works,
    assert_config_valid,
    assert_error_handled,
    assert_performance_within_range,
    assert_metrics_improved,
)

__all__ = [
    # Base Classes
    "BasePolyglotTest",
    "BaseBenchmarkTest",
    "BaseIntegrationTest",
    "BasePerformanceTest",
    # Benchmarking
    "BenchmarkResult",
    "run_benchmark",
    "compare_benchmarks",
    "format_benchmark_result",
    "benchmark_backends",
    # Helpers
    "create_temp_directory",
    "cleanup_temp_directory",
    "create_test_config",
    "create_mock_processor",
    "create_mock_engine",
    "create_test_data_file",
    "load_test_data",
    "assert_dict_contains",
    "retry_on_failure",
    "skip_if_backend_unavailable",
    "measure_time",
    # Fixtures
    "MockInferenceEngine",
    "MockDataProcessor",
    "TestConfig",
    "TestDataGenerator",
    # Assertions
    "assert_engine_works",
    "assert_processor_works",
    "assert_config_valid",
    "assert_error_handled",
    "assert_performance_within_range",
    "assert_metrics_improved",
]
