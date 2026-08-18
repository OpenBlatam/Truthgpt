"""
Unit Tests for Refactored Utils Subpackages and Discovery APIs.
"""

import os
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import utils
from utils import (
    list_available_utility_modules,
    get_utility_module_info,
    list_all_utilities,
    format_bytes,
    timed_block,
    safe_run,
    benchmark_function,
    setup_logger,
    get_logger,
    TrainingLogger,
    visualize_checkpoints,
    summarize_run,
    compare_runs,
    get_run_info,
    TruthGPTConfig,
    create_truthgpt_config,
    create_truthgpt_optimizer,
)


class TestUtilsUnit(unittest.TestCase):
    """Unit tests for core utils functionality."""

    def test_discovery_modules_count(self):
        modules = list_available_utility_modules()
        self.assertGreaterEqual(len(modules), 13)
        self.assertIn("quantum", modules)
        self.assertIn("optimizers", modules)
        self.assertIn("systems", modules)
        self.assertIn("training_tools", modules)

    def test_format_bytes_scales(self):
        self.assertEqual(format_bytes(512), "512.00 B")
        self.assertEqual(format_bytes(2048), "2.00 KB")
        self.assertEqual(format_bytes(10 * 1024 * 1024), "10.00 MB")
        self.assertEqual(format_bytes(2.5 * 1024 * 1024 * 1024), "2.50 GB")

    def test_safe_run_resilience(self):
        result = safe_run(lambda: 42)
        self.assertEqual(result, 42)

        def will_raise():
            raise RuntimeError("Failure")

        result = safe_run(will_raise, default="recovered")
        self.assertEqual(result, "recovered")

    def test_benchmark_runner(self):
        call_count = 0
        def dummy_op():
            nonlocal call_count
            call_count += 1

        stats = benchmark_function(dummy_op, iterations=10, warmup=2)
        self.assertEqual(call_count, 12)
        self.assertGreater(stats["throughput_per_sec"], 0)


if __name__ == "__main__":
    unittest.main()
