"""
Unit tests for core framework and ops modules.
"""

import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)
if PARENT_ROOT not in sys.path:
    sys.path.insert(0, PARENT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)



import torch
import torch.nn as nn
from optimization_core.core.ops.ultra_fast_optimizer import CacheOptimizer, UltraFastOptimizer
from optimization_core.core.framework.result_builder import ResultBuilder
from optimization_core.core.framework.statistics_calculator import StatisticsCalculator
from optimization_core.core.framework.metrics_calculator import AIOptimizationLevel




class TestCoreOpsAndFramework(unittest.TestCase):
    """Tests for refactored core ops and framework components."""

    def test_cache_optimizer_hashlib(self):
        """Verify CacheOptimizer can generate model hash without NameError."""
        model = nn.Sequential(nn.Linear(10, 5))
        cache_opt = CacheOptimizer()
        model_hash = cache_opt._generate_model_hash(model)
        self.assertIsInstance(model_hash, str)
        self.assertEqual(len(model_hash), 32)  # MD5 hex length

    def test_result_builder_safe_defaults(self):
        """Verify ResultBuilder provides safe defaults when metrics keys are missing."""
        model = nn.Sequential(nn.Linear(4, 2))
        partial_metrics = {"speed_improvement": 2.5}
        result = ResultBuilder.build(
            optimized_model=model,
            performance_metrics=partial_metrics,
            optimization_time=0.05,
            optimization_level=AIOptimizationLevel.INTELLIGENT,
            techniques_applied=["quantization"],
            ai_insights={"note": "test"},
        )
        self.assertEqual(result.speed_improvement, 2.5)
        self.assertEqual(result.memory_reduction, 0.0)
        self.assertEqual(result.accuracy_preservation, 1.0)
        self.assertEqual(result.intelligence_score, 1.0)

    def test_statistics_calculator_duck_typing(self):
        """Verify StatisticsCalculator works cleanly with partial objects."""
        class DummyResult:
            speed_improvement = 2.0
            memory_reduction = 0.5

        class DummyLearning:
            def get_learning_history(self):
                return [1, 2]
            def get_experience_buffer(self):
                return [1]
            def get_exploration_rate(self):
                return 0.05

        history = [DummyResult()]
        stats = StatisticsCalculator.calculate(
            optimization_history=history,
            optimization_level=AIOptimizationLevel.GENIUS,
            learning_mechanism=DummyLearning(),
        )
        self.assertEqual(stats["total_optimizations"], 1)
        self.assertEqual(stats["avg_speed_improvement"], 2.0)
        self.assertEqual(stats["avg_memory_reduction"], 0.5)
        self.assertEqual(stats["learning_history_length"], 2)


if __name__ == "__main__":
    unittest.main()
