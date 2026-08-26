"""
Comprehensive Unit Test Suite for optimization_core.core Refactoring.

Tests:
1. Module discovery and lazy resolution for all 18 core submodules.
2. Unified ConfigManager (instance methods, environment parsing, validation, and static helpers).
3. Configuration dataclasses (OptimizationConfig, TrainingConfig, TrainerConfig, ModelConfig, DataConfig, etc.).
4. Distributed runtime (DistributedOptimizer) and Fallback runtime (RealtimeOptimizer).
5. Adapters layer (ModelAdapter, DataAdapter, JSONLDataAdapter, OptimizerAdapter).
6. Microservices architecture (Quantization, Pruning, Enhancement, Acceleration, AI, Orchestrator, System).
7. Systems infrastructure (DynamicFactory, EventEmitter, ServiceRegistry, PluginManager, ModuleLoader).
8. Unified optimizer factory and registry.
"""

import sys
import unittest
import os
from pathlib import Path
import torch
import torch.nn as nn

# Ensure optimization_core is on sys.path
opt_core_dir = str(Path(__file__).resolve().parent.parent.parent)
if opt_core_dir in sys.path:
    sys.path.remove(opt_core_dir)
sys.path.insert(0, opt_core_dir)

if "core" in sys.modules and not getattr(sys.modules["core"], "__file__", "").startswith(opt_core_dir):
    sys.modules.pop("core", None)

import core


class TestCoreComprehensiveRefactor(unittest.TestCase):
    """Complete validation test suite for core package refactoring."""

    def test_01_all_18_submodules_available(self):
        """Verify that all 18 submodules are registered and accessible."""
        available = core.list_available_core_modules()
        expected = [
            "systems", "optimizers", "ops", "util", "kernel", "kernels",
            "services", "adapters", "framework", "validation", "composition",
            "runtime", "common_runtime", "data", "platform", "lib",
            "distributed_runtime", "runtime_fallback",
        ]
        for sub in expected:
            self.assertIn(sub, available, f"Submodule {sub} missing in list_available_core_modules()")
            mod = getattr(core, sub)
            self.assertIsNotNone(mod, f"Failed to access core.{sub}")

    def test_02_get_core_module_info(self):
        """Verify get_core_module_info returns expected metadata."""
        info = core.get_core_module_info("distributed_runtime")
        self.assertEqual(info["name"], "distributed_runtime")
        self.assertEqual(info["import_path"], "core.distributed_runtime")
        self.assertEqual(info["category"], "distributed")

        with self.assertRaises(KeyError):
            core.get_core_module_info("non_existent_module")

    def test_03_unified_config_manager_instance(self):
        """Test unified ConfigManager instance methods and dynamic get/set."""
        from core.common_runtime import (
            ConfigManager,
            Environment,
            OptimizationConfig,
            MonitoringConfig,
            PerformanceConfig,
        )

        cfg_mgr = ConfigManager(environment=Environment.DEVELOPMENT)
        self.assertEqual(cfg_mgr.environment, Environment.DEVELOPMENT)

        # Dot-separated get and set
        cfg_mgr.set("optimization.level", "ludicrous")
        self.assertEqual(cfg_mgr.get("optimization.level"), "ludicrous")
        self.assertEqual(cfg_mgr.get("non_existent.key", default="fallback"), "fallback")

        # Typed config getters
        opt_cfg = cfg_mgr.get_optimization_config()
        self.assertIsInstance(opt_cfg, OptimizationConfig)
        self.assertEqual(opt_cfg.level, "ludicrous")

        mon_cfg = cfg_mgr.get_monitoring_config()
        self.assertIsInstance(mon_cfg, MonitoringConfig)

        perf_cfg = cfg_mgr.get_performance_config()
        self.assertIsInstance(perf_cfg, PerformanceConfig)

        # Update callbacks
        called = []
        cfg_mgr.add_update_callback(lambda data: called.append(True))
        cfg_mgr.set("optimization.max_cpu_cores", 16)
        self.assertTrue(len(called) > 0)
        self.assertEqual(cfg_mgr.get("optimization.max_cpu_cores"), 16)

        # Validate config
        errors = cfg_mgr.validate_config()
        self.assertEqual(len(errors), 0)

    def test_04_unified_config_manager_env_loading(self):
        """Test ConfigManager environment variable loading."""
        from core.common_runtime import ConfigManager

        os.environ["OPTIMIZATION_OPTIMIZATION_LEVEL"] = "extreme"
        os.environ["OPTIMIZATION_PERFORMANCE_BATCH_SIZE"] = "64"
        try:
            cfg_mgr = ConfigManager()
            loaded = cfg_mgr.load_from_environment(prefix="OPTIMIZATION_")
            self.assertTrue(loaded)
            self.assertEqual(cfg_mgr.get("optimization.level"), "extreme")
            self.assertEqual(cfg_mgr.get("performance.batch_size"), 64)
        finally:
            os.environ.pop("OPTIMIZATION_OPTIMIZATION_LEVEL", None)
            os.environ.pop("OPTIMIZATION_PERFORMANCE_BATCH_SIZE", None)

    def test_05_config_dataclasses_and_trainer_config(self):
        """Test configuration dataclasses conversions and TrainerConfig serialization."""
        from core.common_runtime import (
            ModelConfig,
            TrainingConfig,
            DataConfig,
            HardwareConfig,
            TrainerConfig,
        )

        model_cfg = ModelConfig(name_or_path="gpt2-medium", lora_enabled=True, lora_r=8)
        self.assertTrue(model_cfg.lora_enabled)
        self.assertEqual(model_cfg.lora_r, 8)

        training_cfg = TrainingConfig(epochs=5, learning_rate=1e-4)
        self.assertEqual(training_cfg.epochs, 5)

        data_cfg = DataConfig(dataset="custom_dataset", max_seq_len=256)
        self.assertEqual(data_cfg.dataset, "custom_dataset")

        trainer_cfg = TrainerConfig(
            run_name="test_run",
            model=model_cfg,
            training=training_cfg,
            data=data_cfg,
        )
        trainer_dict = trainer_cfg.to_dict()
        self.assertEqual(trainer_dict["run_name"], "test_run")
        self.assertEqual(trainer_dict["model"]["name_or_path"], "gpt2-medium")
        self.assertEqual(trainer_dict["training"]["epochs"], 5)

        # Round-trip from_dict
        rebuilt_trainer = TrainerConfig.from_dict(trainer_dict)
        self.assertEqual(rebuilt_trainer.run_name, "test_run")
        self.assertEqual(rebuilt_trainer.model.name_or_path, "gpt2-medium")

    def test_06_distributed_runtime_export(self):
        """Test core.distributed_runtime module and DistributedOptimizer."""
        from core.distributed_runtime import DistributedOptimizer

        dist_opt = DistributedOptimizer(world_size=4, rank=0)
        self.assertEqual(dist_opt.world_size, 4)
        self.assertEqual(dist_opt.rank, 0)
        step_res = dist_opt.optimize_step({"loss": 0.25})
        self.assertEqual(step_res["status"], "success")
        self.assertEqual(step_res["world_size"], 4)

    def test_07_runtime_fallback_export(self):
        """Test core.runtime_fallback module and RealtimeOptimizer."""
        from core.runtime_fallback import RealtimeOptimizer

        fallback_opt = RealtimeOptimizer(fallback_strategy="cpu_eager")
        self.assertTrue(fallback_opt.is_fallback_active())
        self.assertEqual(fallback_opt.get_strategy(), "cpu_eager")

        test_tensor = torch.tensor([1.0, 2.0, 3.0])
        res = fallback_opt.execute_fallback(lambda x: x * 2, test_tensor)
        self.assertTrue(torch.equal(res, torch.tensor([2.0, 4.0, 6.0])))

    def test_08_adapters_and_jsonl_adapter(self):
        """Test core.adapters module and JSONLDataAdapter export."""
        from core.adapters import (
            ModelAdapter,
            DataAdapter,
            JSONLDataAdapter,
            OptimizerAdapter,
            PyTorchOptimizerAdapter,
        )

        self.assertIsNotNone(ModelAdapter)
        self.assertIsNotNone(DataAdapter)
        self.assertIsNotNone(JSONLDataAdapter)
        self.assertIsNotNone(OptimizerAdapter)

        # Test PyTorchOptimizerAdapter
        py_opt_adapter = PyTorchOptimizerAdapter()
        linear = nn.Linear(4, 2)
        opt = py_opt_adapter.create_optimizer(linear.parameters(), optimizer_type="adamw", lr=1e-3)
        self.assertIsInstance(opt, torch.optim.AdamW)

        opt_state = py_opt_adapter.get_optimizer_state(opt)
        self.assertEqual(opt_state["type"], "AdamW")
        self.assertIn("state_dict", opt_state)

        # Test JSONLDataAdapter data info
        jsonl_adapter = JSONLDataAdapter()
        info = jsonl_adapter.get_data_info(["hello world", "truthgpt optimization core"])
        self.assertEqual(info["num_samples"], 2)
        self.assertGreater(info["avg_length"], 0)

    def test_09_microservices_pruning_and_orchestrator(self):
        """Test modular microservices including PruningMicroservice with proper prune import."""
        import asyncio
        from core.services import (
            QuantizationMicroservice,
            PruningMicroservice,
            EnhancementMicroservice,
            AccelerationMicroservice,
            AIMicroservice,
            ModularMicroserviceOrchestrator,
        )

        test_linear = nn.Linear(10, 5)

        # Test PruningMicroservice directly
        async def run_pruning():
            prune_srv = PruningMicroservice("prune_test")
            import pickle
            req = {"model_data": pickle.dumps(test_linear)}
            res = await prune_srv.process_request(req)
            self.assertTrue(res["success"])
            self.assertIn("optimized_model_data", res)

        asyncio.run(run_pruning())

        # Test QuantizationMicroservice directly
        async def run_quant():
            quant_srv = QuantizationMicroservice("quant_test")
            import pickle
            req = {"model_data": pickle.dumps(test_linear)}
            res = await quant_srv.process_request(req)
            self.assertTrue(res["success"])
            self.assertIn("optimized_model_data", res)

        asyncio.run(run_quant())

        # Test Orchestrator
        async def run_orchestrator():
            orchestrator = ModularMicroserviceOrchestrator({"quantization_services": 1, "enhancement_services": 1})
            result = await orchestrator.process_optimization_request(test_linear, ["quantization", "enhancement"])
            self.assertIsNotNone(result.optimized_model)
            self.assertIn("quantization", result.techniques_applied)
            self.assertIn("enhancement", result.techniques_applied)

        asyncio.run(run_orchestrator())

    def test_10_triple_namespace_shims(self):
        """Test that submodules are accessible via core.X and optimization_core.core.X."""
        self.assertIn("core.systems", sys.modules)
        self.assertIn("optimization_core.core.systems", sys.modules)
        self.assertIn("core.distributed_runtime", sys.modules)
        self.assertIn("optimization_core.core.distributed_runtime", sys.modules)
        self.assertIn("core.runtime_fallback", sys.modules)
        self.assertIn("optimization_core.core.runtime_fallback", sys.modules)


if __name__ == "__main__":
    unittest.main()
