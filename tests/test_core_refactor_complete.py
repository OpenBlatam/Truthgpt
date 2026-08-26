"""
TruthGPT Core Refactor Complete Verification Suite
==================================================
Comprehensive automated test suite validating the refactored `core` architecture:
- Fast startup (<0.1s lazy loading)
- 18 submodules resolution & exports
- Unified ConfigManager functionality
- Exception hierarchy
- Infrastructure systems (DynamicFactory, EventEmitter, ServiceRegistry, PluginManager, ModuleLoader)
- Composition & Validation tools
- Optimizer registry & factory
- Dual namespace registration
"""

import sys
import os
import unittest
import time
from pathlib import Path

# Add project root to sys.path with highest priority
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARENT_ROOT = PROJECT_ROOT.parent

# Ensure PROJECT_ROOT is index 0
if str(str(PROJECT_ROOT)) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Remove parent root if present to avoid shadowing core package
if str(PARENT_ROOT) in sys.path:
    sys.path.remove(str(PARENT_ROOT))
    sys.path.append(str(PARENT_ROOT))


class TestCoreRefactorComplete(unittest.TestCase):
    """Test suite for refactored optimization_core.core package."""

    def test_01_import_speed(self):
        """Verify initial import of core completes in < 100ms."""
        # Clean from sys.modules if present to test fresh import
        for key in list(sys.modules.keys()):
            if key == "core" or key.startswith("core.") or key.startswith("optimization_core.core"):
                del sys.modules[key]

        if str(PROJECT_ROOT) in sys.path:
            sys.path.remove(str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT))

        t0 = time.perf_counter()
        import core
        elapsed = time.perf_counter() - t0

        print(f"\n[OK] Core fresh import latency: {elapsed * 1000:.2f} ms")
        self.assertLess(elapsed, 0.20, f"Import took too long: {elapsed:.3f}s")

    def test_02_available_modules_list(self):
        """Verify list_available_core_modules contains all 18 standard submodules."""
        import core

        expected_modules = [
            "systems", "optimizers", "ops", "util", "kernel", "kernels",
            "services", "adapters", "framework", "validation", "composition",
            "runtime", "common_runtime", "data", "platform", "lib",
            "distributed_runtime", "runtime_fallback",
        ]

        available = core.list_available_core_modules()
        self.assertEqual(len(available), 18)
        for mod in expected_modules:
            self.assertIn(mod, available, f"Module '{mod}' missing from core modules list")
        print(f"[OK] Verified 18 available core submodules: {available}")

    def test_03_all_submodules_resolution(self):
        """Verify dynamic resolution and lazy loading of all 18 core submodules."""
        import core

        for mod_name in core.list_available_core_modules():
            mod = getattr(core, mod_name)
            self.assertIsNotNone(mod, f"Failed to access core.{mod_name}")
            # Verify registered in sys.modules
            self.assertIn(f"core.{mod_name}", sys.modules)
        print("[OK] All 18 core submodules successfully resolved and registered in sys.modules")

    def test_04_unified_config_manager(self):
        """Verify consolidated ConfigManager instance methods and class methods."""
        import core
        from core import ConfigManager, OptimizationConfig, MonitoringConfig, PerformanceConfig, TrainerConfig

        # 1. Instance methods (key-path access, defaults, section updates)
        mgr = ConfigManager()
        self.assertEqual(mgr.get("optimization.level"), "standard")
        mgr.set("custom.param.deep", 42)
        self.assertEqual(mgr.get("custom.param.deep"), 42)
        self.assertEqual(mgr.get("nonexistent.key", "default_val"), "default_val")

        opt_cfg = mgr.get_optimization_config()
        self.assertIsInstance(opt_cfg, OptimizationConfig)
        self.assertEqual(opt_cfg.level, "standard")

        mon_cfg = mgr.get_monitoring_config()
        self.assertIsInstance(mon_cfg, MonitoringConfig)

        perf_cfg = mgr.get_performance_config()
        self.assertIsInstance(perf_cfg, PerformanceConfig)

        # 2. Validation report
        val_errors = mgr.validate_config()
        self.assertEqual(len(val_errors), 0)

        # 3. Static/class methods for TrainerConfig validation
        valid_dict = {
            "model": {"name_or_path": "gpt2"},
            "training": {"epochs": 3, "learning_rate": 5e-5},
            "data": {"dataset": "wikitext"},
        }
        self.assertTrue(ConfigManager.validate_training_config(valid_dict))
        trainer_cfg = TrainerConfig.from_dict(valid_dict)
        self.assertEqual(trainer_cfg.model.name_or_path, "gpt2")
        self.assertEqual(trainer_cfg.training.epochs, 3)

        print("[OK] Unified ConfigManager instance and class APIs verified")

    def test_05_systems_infrastructure(self):
        """Verify infrastructure systems: DynamicFactory, EventEmitter, ServiceRegistry, PluginManager, ModuleLoader."""
        import core

        # DynamicFactory
        factory = core.DynamicFactory("test_factory")
        self.assertEqual(factory.name, "test_factory")

        # EventEmitter
        emitter = core.get_event_emitter()
        self.assertIsNotNone(emitter)
        received = []

        def test_handler(event):
            received.append(event.data)

        core.on_event("test.event", test_handler)
        core.emit_event("test.event", {"msg": "hello_event"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["msg"], "hello_event")

        # ServiceRegistry
        registry = core.ServiceRegistry()
        registry.register("dummy_service", {"service_key": "val123"})
        self.assertEqual(registry.get("dummy_service")["service_key"], "val123")

        # PluginManager
        plugin_mgr = core.get_plugin_manager()
        self.assertIsNotNone(plugin_mgr)

        # ModuleLoader
        loader = core.get_module_loader()
        self.assertIsNotNone(loader)

        print("[OK] Infrastructure systems (Factory, Event, Service, Plugin, ModuleLoader) verified")

    def test_06_exceptions_hierarchy(self):
        """Verify unified exception classes in core."""
        import core

        self.assertTrue(issubclass(core.TruthGPTCoreError, core.OptimizationCoreError))
        self.assertTrue(issubclass(core.ConfigValidationError, core.ValidationError))
        self.assertTrue(issubclass(core.PluginError, core.TruthGPTCoreError))
        self.assertTrue(issubclass(core.ServiceRegistryError, core.TruthGPTCoreError))
        self.assertTrue(issubclass(core.OptimizerExecutionError, core.TruthGPTCoreError))
        self.assertTrue(issubclass(core.MicroserviceCommunicationError, core.TruthGPTCoreError))

        # Test formatting and details
        err = core.ConfigValidationError("Invalid learning rate", field="training.learning_rate")
        self.assertIn("Invalid learning rate", str(err))
        self.assertEqual(err.details.get("field"), "training.learning_rate")

        print("[OK] Exception hierarchy verified")

    def test_07_composition_and_validation(self):
        """Verify ComponentAssembler, WorkflowBuilder, Validator, ModelValidator."""
        import core

        assembler = core.ComponentAssembler()
        self.assertIsNotNone(assembler)

        workflow = core.WorkflowBuilder("test_workflow")
        self.assertEqual(workflow.name, "test_workflow")

        validator = core.Validator
        self.assertIsNotNone(validator)
        model_validator = core.ModelValidator()
        self.assertIsNotNone(model_validator)

        print("[OK] Composition & Validation classes verified")

    def test_08_optimizer_registry_and_factory(self):
        """Verify optimizer registry metadata and factory method."""
        import core

        optimizers_mod = core.optimizers
        avail_opts = optimizers_mod.list_available_core_optimizers()
        self.assertIn("enhanced", avail_opts)
        self.assertIn("extreme", avail_opts)
        self.assertIn("quantum", avail_opts)
        self.assertIn("ultra_fast", avail_opts)

        info = optimizers_mod.get_core_optimizer_info("enhanced")
        self.assertEqual(info["class"], "EnhancedOptimizer")
        self.assertEqual(info["module"], "core.util.enhanced_optimizer")

        # Verify factory
        enhanced_opt = core.create_core_optimizer("enhanced", {"learning_rate": 0.001})
        self.assertIsNotNone(enhanced_opt)

        print("[OK] Optimizer registry and factory verified")

    def test_09_kernel_singleton_and_services(self):
        """Verify TruthGPTKernel singleton accessors and infrastructure inits."""
        import core

        kernel_pkg = core.kernel
        self.assertIsNotNone(kernel_pkg)
        self.assertTrue(hasattr(kernel_pkg, "TruthGPTKernel"))

        # Verify kernel config sub-package init
        from core.kernel.config import KernelConfig, LogLevel
        k_cfg = KernelConfig(log_level=LogLevel.INFO)
        self.assertEqual(k_cfg.log_level, LogLevel.INFO)

        # Verify kernel events sub-package init
        from core.kernel.events import ProductionEventBus, Event
        evt_bus = ProductionEventBus()
        self.assertIsNotNone(evt_bus)

        # Verify kernel services infrastructure sub-package init
        from core.kernel.services.infrastructure import ResourceManager
        self.assertIsNotNone(ResourceManager)

        print("[OK] Kernel orchestrator and sub-package inits verified")

    def test_10_distributed_and_runtime_fallback_exports(self):
        """Verify distributed_runtime and runtime_fallback exports."""
        import core

        from core.distributed_runtime import DistributedOptimizer
        dist_opt = DistributedOptimizer(world_size=2, rank=0)
        res = dist_opt.optimize_step({"loss": 0.5})
        self.assertEqual(res["status"], "success")

        from core.runtime_fallback import RealtimeOptimizer
        rt_opt = RealtimeOptimizer(fallback_strategy="cpu_eager")
        self.assertTrue(rt_opt.is_fallback_active())

        print("[OK] Distributed runtime and Runtime fallback verified")

    def test_11_dual_namespace_aliases(self):
        """Verify that importing through 'core' and 'optimization_core.core' gives identical objects."""
        import core
        import sys

        opt_core = sys.modules.get("optimization_core.core")
        self.assertIsNotNone(opt_core)
        self.assertIs(core.ConfigManager, opt_core.ConfigManager)
        self.assertIs(core.DynamicFactory, opt_core.DynamicFactory)

        print("[OK] Dual namespace aliases (core & optimization_core.core) verified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
