"""
Unit and Integration Tests for Refactored Optimization Core Utils
=================================================================
Validates subpackage discovery, lazy loading across all 13 submodules,
foundational helpers, structured logging, visualization tools, run comparison,
cleanup utilities, and dual namespace compatibility.
"""

import importlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Ensure optimization_core is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    # Discovery functions
    list_available_utility_modules,
    get_utility_module_info,
    list_all_utilities,
    # Foundational helpers
    format_bytes,
    get_gpu_info,
    get_memory_info,
    timed_block,
    safe_run,
    benchmark_function,
    BaseOptimizationModel,
    CudaResourceManager,
    system_metrics_collector,
    # Logging
    setup_logger,
    get_logger,
    TrainingLogger,
    # Training tools & visualization
    visualize_checkpoints,
    summarize_run,
    plot_loss_curves,
    visualize_memory_profile,
    compare_runs,
    get_run_info,
    cleanup_runs,
    cleanup_old_runs,
    cleanup_checkpoints,
    # TruthGPT Core
    TruthGPTConfig,
    create_truthgpt_config,
    create_truthgpt_optimizer,
    OptimizationLevel,
    DeviceType,
    PrecisionType,
)


class TestUtilsSubmodulesDiscovery(unittest.TestCase):
    """Test submodule registration, metadata querying, and category overviews."""

    def test_list_available_utility_modules(self):
        available = list_available_utility_modules()
        expected = [
            "truthgpt", "optimizers", "systems", "training_tools",
            "adapters", "ai", "enterprise", "gpu", "memory",
            "monitoring", "quantum", "training", "modules"
        ]
        for name in expected:
            self.assertIn(name, available)

    def test_get_utility_module_info(self):
        info = get_utility_module_info("truthgpt")
        self.assertEqual(info["name"], "truthgpt")
        self.assertIn("truthgpt", info["import_path"])

        with self.assertRaises(ValueError):
            get_utility_module_info("non_existent_module_xyz")

    def test_list_all_utilities(self):
        overview = list_all_utilities()
        self.assertIn("submodules", overview)
        self.assertIn("base", overview)
        self.assertIn("logging", overview)
        self.assertIn("training_tools", overview)
        self.assertIn("truthgpt", overview)
        self.assertIn("gpu", overview)
        self.assertIn("memory", overview)


class TestUtilsLazySubmodules(unittest.TestCase):
    """Test dynamic attribute access and component resolution across all subpackages."""

    def test_quantum_subpackage(self):
        self.assertIsNotNone(utils.quantum)
        from utils.quantum import (
            QuantumUtils,
            UniversalQuantumOptimizer,
            list_available_quantum_components,
            get_quantum_component_info,
        )
        self.assertIsNotNone(QuantumUtils)
        self.assertIsNotNone(UniversalQuantumOptimizer)
        components = list_available_quantum_components()
        self.assertIn("QuantumUtils", components)
        self.assertIn("UniversalQuantumOptimizer", components)
        info = get_quantum_component_info("QuantumUtils")
        self.assertEqual(info["name"], "QuantumUtils")

    def test_optimizers_subpackage(self):
        self.assertIsNotNone(utils.optimizers)
        from utils.optimizers import (
            HyperSpeedOptimizer,
            AutoPerformanceOptimizer,
            UltraAIOptimizer,
            UniversalQuantumOptimizer,
            AdvancedAIOptimizer,
            list_available_optimizers,
            get_optimizer_info,
        )
        self.assertIsNotNone(HyperSpeedOptimizer)
        self.assertIsNotNone(AutoPerformanceOptimizer)
        self.assertIsNotNone(UltraAIOptimizer)
        self.assertIsNotNone(UniversalQuantumOptimizer)
        self.assertIsNotNone(AdvancedAIOptimizer)
        opt_list = list_available_optimizers()
        self.assertIn("HyperSpeedOptimizer", opt_list)
        info = get_optimizer_info("HyperSpeedOptimizer")
        self.assertEqual(info["name"], "HyperSpeedOptimizer")

    def test_systems_subpackage(self):
        self.assertIsNotNone(utils.systems)
        from utils.systems import (
            SyntheticMultiverseOptimizationSystem,
            TensorFlowIntegrationSystem,
            QuantumDeepLearningSystem,
            FederatedLearningSystem,
            list_available_systems,
            get_system_info,
        )
        self.assertIsNotNone(SyntheticMultiverseOptimizationSystem)
        self.assertIsNotNone(TensorFlowIntegrationSystem)
        self.assertIsNotNone(QuantumDeepLearningSystem)
        self.assertIsNotNone(FederatedLearningSystem)
        sys_list = list_available_systems()
        self.assertIn("SyntheticMultiverseOptimizationSystem", sys_list)
        info = get_system_info("SyntheticMultiverseOptimizationSystem")
        self.assertEqual(info["name"], "SyntheticMultiverseOptimizationSystem")

    def test_training_tools_subpackage(self):
        self.assertIsNotNone(utils.training_tools)
        from utils.training_tools import (
            visualize_checkpoints,
            summarize_run,
            compare_runs,
            get_run_info,
            cleanup_runs,
            list_available_training_tools,
            get_training_tool_info,
        )
        self.assertTrue(callable(visualize_checkpoints))
        self.assertTrue(callable(summarize_run))
        self.assertTrue(callable(compare_runs))
        self.assertTrue(callable(get_run_info))
        self.assertTrue(callable(cleanup_runs))
        tools = list_available_training_tools()
        self.assertIn("visualize_checkpoints", tools)
        self.assertIn("compare_runs", tools)

    def test_adapters_subpackage(self):
        self.assertIsNotNone(utils.adapters)
        from utils.adapters import (
            EnterpriseTruthGPTAdapter,
            TruthGPTIntegration,
            TruthGPTEnhancedUtils,
            TruthGPTCore,
            list_available_adapter_components,
        )
        self.assertIsNotNone(EnterpriseTruthGPTAdapter)
        self.assertIsNotNone(TruthGPTIntegration)
        self.assertIsNotNone(TruthGPTEnhancedUtils)
        self.assertIsNotNone(TruthGPTCore)
        self.assertIn("EnterpriseTruthGPTAdapter", list_available_adapter_components())

    def test_ai_subpackage(self):
        self.assertIsNotNone(utils.ai)
        from utils.ai import (
            UltraAIOptimizer,
            AIUtils,
            UltraAutonomousAgent,
            UltraMachineLearningOptimizer,
            list_available_ai_components,
        )
        self.assertIsNotNone(UltraAIOptimizer)
        self.assertIsNotNone(AIUtils)
        self.assertIsNotNone(UltraAutonomousAgent)
        self.assertIsNotNone(UltraMachineLearningOptimizer)
        self.assertIn("UltraAIOptimizer", list_available_ai_components())

    def test_enterprise_subpackage(self):
        self.assertIsNotNone(utils.enterprise)
        from utils.enterprise import (
            EnterpriseAuth,
            EnterpriseCache,
            EnterpriseMonitor,
            EnterpriseMetrics,
            EnterpriseCloudIntegration,
            list_available_enterprise_components,
        )
        self.assertIsNotNone(EnterpriseAuth)
        self.assertIsNotNone(EnterpriseCache)
        self.assertIsNotNone(EnterpriseMonitor)
        self.assertIsNotNone(EnterpriseMetrics)
        self.assertIsNotNone(EnterpriseCloudIntegration)
        self.assertIn("EnterpriseAuth", list_available_enterprise_components())

    def test_gpu_subpackage(self):
        self.assertIsNotNone(utils.gpu)
        from utils.gpu import (
            GPUUtils,
            CUDAOptimizations,
            OptimizedLayerNorm,
            OptimizedRMSNorm,
            list_available_gpu_components,
        )
        self.assertIsNotNone(GPUUtils)
        self.assertIsNotNone(CUDAOptimizations)
        self.assertIsNotNone(OptimizedLayerNorm)
        self.assertIsNotNone(OptimizedRMSNorm)
        self.assertIn("GPUUtils", list_available_gpu_components())

    def test_memory_subpackage(self):
        self.assertIsNotNone(utils.memory)
        from utils.memory import (
            MemoryOptimizer,
            MemoryOptimizationConfig,
            TensorPool,
            ActivationCache,
            MemoryUtils,
            list_available_memory_components,
        )
        self.assertIsNotNone(MemoryOptimizer)
        self.assertIsNotNone(MemoryOptimizationConfig)
        self.assertIsNotNone(TensorPool)
        self.assertIsNotNone(ActivationCache)
        self.assertIsNotNone(MemoryUtils)
        self.assertIn("MemoryOptimizer", list_available_memory_components())

    def test_monitoring_subpackage(self):
        self.assertIsNotNone(utils.monitoring)
        from utils.monitoring import (
            RealTimePerformanceMonitor,
            TruthGPTMonitoring,
            visualize_checkpoints,
            compare_runs,
            list_available_monitoring_components,
        )
        self.assertIsNotNone(RealTimePerformanceMonitor)
        self.assertIsNotNone(TruthGPTMonitoring)
        self.assertTrue(callable(visualize_checkpoints))
        self.assertTrue(callable(compare_runs))
        self.assertIn("RealTimePerformanceMonitor", list_available_monitoring_components())

    def test_training_subpackage(self):
        self.assertIsNotNone(utils.training)
        from utils.training import (
            TruthGPTTrainingUtils,
            TruthGPTAdvancedTraining,
            TruthGPTOptimizationUtils,
            TruthGPTEvaluationUtils,
            list_available_training_components,
        )
        self.assertIsNotNone(TruthGPTTrainingUtils)
        self.assertIsNotNone(TruthGPTAdvancedTraining)
        self.assertIsNotNone(TruthGPTOptimizationUtils)
        self.assertIsNotNone(TruthGPTEvaluationUtils)
        self.assertIn("TruthGPTTrainingUtils", list_available_training_components())


class TestUtilsFoundationalHelpers(unittest.TestCase):
    """Test byte formatting, timing blocks, safe runner, and benchmarking."""

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(-10), "0 B")

    def test_timed_block(self):
        with timed_block("TestSleep") as t:
            time.sleep(0.01)
        self.assertGreater(t["elapsed_sec"], 0.005)

    def test_safe_run(self):
        def risky(x):
            if x == 0:
                raise ValueError("Div zero")
            return 10 / x

        self.assertEqual(safe_run(risky, 2), 5.0)
        self.assertIsNone(safe_run(risky, 0))
        self.assertEqual(safe_run(risky, 0, default=-1), -1)

    def test_benchmark_function(self):
        def add_numbers(a, b):
            return a + b

        res = benchmark_function(add_numbers, 10, 20, iterations=5, warmup=1)
        self.assertIn("avg_ms", res)
        self.assertIn("min_ms", res)
        self.assertIn("max_ms", res)
        self.assertIn("throughput_per_sec", res)
        self.assertEqual(res["iterations"], 5.0)

    def test_get_gpu_info_and_memory_info(self):
        gpu_info = get_gpu_info()
        self.assertIsInstance(gpu_info, dict)
        self.assertIn("device", gpu_info)
        self.assertIn("available", gpu_info)

        mem_info = get_memory_info()
        self.assertIsInstance(mem_info, dict)
        self.assertIn("cpu_percent", mem_info)
        self.assertIn("memory_used_gb", mem_info)

    def test_base_optimization_model(self):
        class DummyModel(BaseOptimizationModel):
            name: str = "Test"
            value: int = 100

        m = DummyModel(name="TruthGPT", value=42)
        self.assertEqual(m.name, "TruthGPT")
        summary = m.to_summary()
        self.assertEqual(summary["name"], "TruthGPT")
        self.assertEqual(summary["value"], 42)


class TestLoggingUtils(unittest.TestCase):
    """Test structured logger setup and TrainingLogger methods."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_setup_logger_and_training_logger(self):
        log_file = os.path.join(self.test_dir, "test.log")
        logger = setup_logger("test_logger_unique", log_file=log_file)
        self.assertIsNotNone(logger)

        t_logger = TrainingLogger(logger)
        t_logger.log_step(step=1, epoch=1, loss=0.5, learning_rate=1e-4, tokens_per_sec=1200.0)
        t_logger.log_eval(step=10, val_loss=0.45, perplexity=1.56, improved=True)
        t_logger.log_checkpoint(step=10, path="checkpoints/step_10.pt", is_best=True)
        t_logger.log_info("Info test message", batch_size=32)
        t_logger.log_warning("Warning test message")
        t_logger.log_error(ValueError("Sample error"), context="Forward Pass")

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Step 1", content)
            self.assertIn("Val Loss: 0.4500", content)
            self.assertIn("BEST saved at step 10", content)


class TestVisualizationAndRunTools(unittest.TestCase):
    """Test training run summarization, checkpoint visualization, and run cleanup."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.run_dir = os.path.join(self.test_dir, "run_experiment_1")
        os.makedirs(self.run_dir, exist_ok=True)

        # Create dummy checkpoints
        Path(os.path.join(self.run_dir, "step_100.pt")).write_bytes(b"0" * 2048)
        Path(os.path.join(self.run_dir, "best.pt")).write_bytes(b"0" * 4096)
        Path(os.path.join(self.run_dir, "last.pt")).write_bytes(b"0" * 4096)

        # Create dummy config and metrics
        with open(os.path.join(self.run_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"model": "gpt2", "epochs": 5}, f)
        with open(os.path.join(self.run_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump({"final_loss": 0.25}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_summarize_run(self):
        summary = summarize_run(self.run_dir)
        self.assertEqual(summary["name"], "run_experiment_1")
        self.assertTrue(summary["exists"])
        self.assertTrue(summary["has_best"])
        self.assertTrue(summary["has_last"])
        self.assertEqual(len(summary["checkpoints"]), 3)
        self.assertEqual(summary["config"]["model"], "gpt2")
        self.assertEqual(summary["metrics"]["final_loss"], 0.25)

    def test_visualize_checkpoints(self):
        report_file = os.path.join(self.test_dir, "report.txt")
        result = visualize_checkpoints(self.run_dir, save_path=report_file)
        self.assertIn("report_text", result)
        self.assertTrue(os.path.exists(report_file))
        with open(report_file, "r", encoding="utf-8") as f:
            text = f.read()
            self.assertIn("run_experiment_1", text)
            self.assertIn("[BEST]", text)
            self.assertIn("[LATEST]", text)

    def test_get_run_info_and_compare_runs(self):
        info = get_run_info(Path(self.run_dir))
        self.assertEqual(info["name"], "run_experiment_1")
        self.assertTrue(info["has_best"])
        self.assertTrue(info["has_last"])
        self.assertEqual(len(info["checkpoints"]), 3)

        # Test compare runs execution
        compare_runs(self.test_dir)

    def test_cleanup_runs(self):
        # Create an extra run
        extra_run = os.path.join(self.test_dir, "run_old")
        os.makedirs(extra_run, exist_ok=True)
        Path(os.path.join(extra_run, "step_50.pt")).write_bytes(b"0" * 1024)

        # Test dry-run
        cleanup_runs(self.test_dir, days=0, dry_run=True)
        self.assertTrue(os.path.exists(extra_run))

        # Test actual deletion
        cleanup_runs(self.test_dir, days=0, dry_run=False)
        self.assertFalse(os.path.exists(extra_run))

    def test_plot_loss_curves_and_memory_profile(self):
        loss_hist = [1.0, 0.8, 0.5, 0.3, 0.2]
        val_hist = [1.1, 0.85, 0.55, 0.35, 0.22]
        # Should not raise exception
        plot_loss_curves(loss_hist, val_hist, output_path=None)

        profile_data = {
            "peak_gpu_memory_mb": 512.0,
            "allocated_gpu_memory_mb": 256.0,
            "reserved_gpu_memory_mb": 768.0,
            "system_ram_used_gb": 8.0,
        }
        mem_profile = visualize_memory_profile(profile_data)
        self.assertIn("report_text", mem_profile)
        self.assertIn("512.00 MB", mem_profile["report_text"])


class TestTruthGPTCoreUtils(unittest.TestCase):
    """Test TruthGPT configuration and factory helpers."""

    def test_create_truthgpt_config(self):
        cfg = create_truthgpt_config(
            optimization_level="advanced",
            device_type="cpu",
            precision_type="fp32",
        )
        self.assertEqual(cfg.optimization_level, OptimizationLevel.ADVANCED)
        self.assertEqual(cfg.device_type, DeviceType.CPU)
        self.assertEqual(cfg.precision_type, PrecisionType.FP32)

    def test_create_truthgpt_optimizer(self):
        cfg = create_truthgpt_config(
            optimization_level="basic",
            device_type="cpu",
            precision_type="fp32",
        )
        opt = create_truthgpt_optimizer(cfg)
        self.assertIsNotNone(opt)


class TestDualNamespaceCompatibility(unittest.TestCase):
    """Test seamless aliasing between 'utils' and 'optimization_core.utils'."""

    def test_direct_and_prefixed_imports(self):
        import utils as direct_utils
        import optimization_core.utils as opt_utils

        self.assertEqual(direct_utils.format_bytes(1024), opt_utils.format_bytes(1024))
        self.assertIs(direct_utils.setup_logger, opt_utils.setup_logger)
        self.assertIs(direct_utils.TruthGPTConfig, opt_utils.TruthGPTConfig)
        self.assertIs(direct_utils.visualize_checkpoints, opt_utils.visualize_checkpoints)


if __name__ == "__main__":
    unittest.main()
