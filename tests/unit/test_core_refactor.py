"""
Unit tests for Core Module Refactoring.
Verifies module exports, optimizer factories, data caching, framework pipeline, training pipeline, and backward compatibility shims.
"""

import unittest
import sys
from pathlib import Path

opt_core_dir = str(Path(__file__).resolve().parent.parent.parent)
if opt_core_dir in sys.path:
    sys.path.remove(opt_core_dir)
sys.path.insert(0, opt_core_dir)

if "core" in sys.modules and not getattr(sys.modules["core"], "__file__", "").startswith(opt_core_dir):
    sys.modules.pop("core", None)

import torch
import torch.nn as nn

import core
from core import (
    ConfigManager,
    TruthGPTCoreError,
    ServiceRegistry,
    EventEmitter,
    PluginManager,
    DynamicFactory,
    ComponentAssembler,
    WorkflowBuilder,
    Validator,
    ModuleLoader,
    list_available_core_modules,
    get_core_module_info,
)


class TestCoreModuleRefactor(unittest.TestCase):
    """Test suite for optimization_core.core refactored modules."""

    def test_core_top_level_imports(self):
        """Test top-level core module exports and submodules listing."""
        submodules = list_available_core_modules()
        self.assertIn("framework", submodules)
        self.assertIn("optimizers", submodules)
        self.assertIn("data", submodules)
        self.assertIn("systems", submodules)
        self.assertIn("common_runtime", submodules)
        self.assertIn("adapters", submodules)
        self.assertIn("services", submodules)
        self.assertIn("validation", submodules)
        self.assertIn("composition", submodules)

    def test_core_module_info_discovery(self):
        """Test get_core_module_info for metadata discovery."""
        info = get_core_module_info("systems")
        self.assertEqual(info["name"], "systems")
        self.assertEqual(info["import_path"], "core.systems")
        self.assertEqual(info["category"], "infrastructure")

        with self.assertRaises(KeyError):
            get_core_module_info("non_existent_module")

    def test_framework_exports(self):
        """Test framework module exports including TrainingPipeline."""
        from core.framework import (
            OptimizationPipeline,
            TrainingPipeline,
            ResultBuilder,
            StatisticsCalculator,
            ModelFeatureExtractor,
            StrategySelector,
            MetricsCalculator,
            AIOptimizationLevel,
            AIOptimizationResult,
            LearningMechanism,
            InsightsGenerator,
        )

        self.assertIsNotNone(OptimizationPipeline)
        self.assertIsNotNone(TrainingPipeline)
        self.assertIsNotNone(ResultBuilder)
        self.assertIsNotNone(StatisticsCalculator)
        self.assertIsNotNone(AIOptimizationLevel.INTELLIGENT)

    def test_core_optimizers_factory(self):
        """Test unified optimizer creation for base, unified, and enhanced optimizers."""
        from core.optimizers import (
            create_core_optimizer,
            list_available_core_optimizers,
            get_core_optimizer_info,
            BaseTruthGPTOptimizer,
            UnifiedTruthGPTOptimizer,
        )

        available_optimizers = list_available_core_optimizers()
        self.assertIn("base", available_optimizers)
        self.assertIn("unified", available_optimizers)
        self.assertIn("enhanced", available_optimizers)

        info = get_core_optimizer_info("base")
        self.assertEqual(info["class"], "BaseTruthGPTOptimizer")

        base_opt = create_core_optimizer("base", {"learning_rate": 0.001})
        self.assertIsInstance(base_opt, BaseTruthGPTOptimizer)

        unified_opt = create_core_optimizer("unified", {"level": "ludicrous"})
        self.assertIsInstance(unified_opt, UnifiedTruthGPTOptimizer)

        test_model = nn.Linear(10, 2)
        opt_model = unified_opt.optimize(test_model)
        self.assertIsNotNone(opt_model)

    def test_data_caching_system(self):
        """Test data caching, CacheManager, and CacheUtils."""
        from core.data import DataCache, CacheManager, CacheUtils, get_cache_manager

        cache = DataCache(max_size=5, ttl_seconds=60)
        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.size(), 1)

        cache_mgr = get_cache_manager()
        pool = cache_mgr.get_cache("test_pool")
        pool.put("foo", 123)
        self.assertEqual(pool.get("foo"), 123)

        generated_key = CacheUtils.generate_key("prefix", {"a": 1, "b": 2})
        self.assertTrue(generated_key.startswith("prefix:"))

        ser = CacheUtils.serialize_value({"hello": "world"})
        deser = CacheUtils.deserialize_value(ser)
        self.assertEqual(deser, {"hello": "world"})

    def test_common_runtime_utilities(self):
        """Test metrics, monitoring, paper base, and performance utilities."""
        from core.common_runtime import (
            MetricCollector,
            PerformanceMonitor,
            PaperImplementationBase,
            measure_latency,
            measure_model_memory,
        )

        collector = MetricCollector()
        collector.record({"loss": 0.5, "acc": 0.9})
        collector.record({"loss": 0.3, "acc": 0.95})
        summary = collector.get_summary()
        self.assertAlmostEqual(summary["avg_loss"], 0.4)
        self.assertAlmostEqual(summary["avg_acc"], 0.925)

        monitor = PerformanceMonitor("test_mon")
        monitor.start()
        dummy_sum = sum(range(1000))
        elapsed = monitor.stop()
        stats = monitor.get_stats()
        self.assertGreaterEqual(elapsed, 0.0)
        self.assertEqual(stats["name"], "test_mon")

        linear_layer = nn.Linear(100, 50)
        mem_mb = measure_model_memory(linear_layer)
        self.assertGreater(mem_mb, 0.0)

        latency_info = measure_latency(lambda: linear_layer(torch.randn(1, 100)), num_runs=3)
        self.assertIn("avg_latency_ms", latency_info)

    def test_adapters_services_validation_composition(self):
        """Test adapter, service, validation, and composition submodule imports."""
        from core.adapters import ModelAdapter, DataAdapter, OptimizerAdapter
        from core.services import BaseService, ModelService, TrainingService, InferenceService
        from core.validation import Validator, ModelValidator, DataValidator, ConfigValidator
        from core.composition import ComponentAssembler, WorkflowBuilder

        self.assertIsNotNone(ModelAdapter)
        self.assertIsNotNone(BaseService)
        self.assertIsNotNone(Validator)
        self.assertIsNotNone(ComponentAssembler)


if __name__ == "__main__":
    unittest.main()
