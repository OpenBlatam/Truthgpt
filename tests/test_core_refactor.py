"""
Tests for optimization_core.core package structure and refactoring.
"""

import sys
import os
import unittest
import warnings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)
if PARENT_ROOT not in sys.path:
    sys.path.insert(0, PARENT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if "core" in sys.modules and not hasattr(sys.modules["core"], "list_available_core_modules"):
    del sys.modules["core"]


class TestCoreRefactor(unittest.TestCase):

    def test_core_submodules_list(self):
        from core import list_available_core_modules
        modules = list_available_core_modules()
        expected = [
            "systems", "optimizers", "ops", "util", "kernel", "kernels",
            "services", "adapters", "framework", "validation", "composition",
            "runtime", "common_runtime", "data", "platform", "lib",
            "distributed_runtime", "runtime_fallback"
        ]
        for mod in expected:
            self.assertIn(mod, modules)

    def test_lazy_imports(self):
        import core
        self.assertIsNotNone(core.ops)
        self.assertIsNotNone(core.util)
        self.assertIsNotNone(core.framework)
        self.assertIsNotNone(core.systems)
        self.assertIsNotNone(core.optimizers)
        self.assertIsNotNone(core.services)
        self.assertIsNotNone(core.validation)

    def test_ops_exports(self):
        from core.ops import (
            ExtremeOptimizer,
            QuantumOptimizer,
            UltraFastOptimizer,
        )
        self.assertIsNotNone(ExtremeOptimizer)
        self.assertIsNotNone(QuantumOptimizer)
        self.assertIsNotNone(UltraFastOptimizer)

    def test_util_exports(self):
        from core.util import (
            EnhancedOptimizer,
            ComplementaryOptimizer,
            AdvancedComplementaryOptimizer,
            MicroservicesOptimizer,
        )
        self.assertIsNotNone(EnhancedOptimizer)
        self.assertIsNotNone(ComplementaryOptimizer)
        self.assertIsNotNone(AdvancedComplementaryOptimizer)
        self.assertIsNotNone(MicroservicesOptimizer)

    def test_framework_exports(self):
        from core.framework import (
            OptimizationPipeline,
            ResultBuilder,
            StatisticsCalculator,
            StrategySelector,
            AIExtremeOptimizer,
            NeuralOptimizationNetwork,
            ModelFeatureExtractor,
        )
        self.assertIsNotNone(OptimizationPipeline)
        self.assertIsNotNone(ResultBuilder)
        self.assertIsNotNone(StatisticsCalculator)
        self.assertIsNotNone(StrategySelector)
        self.assertIsNotNone(AIExtremeOptimizer)
        self.assertIsNotNone(NeuralOptimizationNetwork)
        self.assertIsNotNone(ModelFeatureExtractor)

    def test_services_exports(self):
        from core.services import (
            BaseService,
            ModelService,
            TrainingService,
            InferenceService,
        )
        self.assertIsNotNone(BaseService)
        self.assertIsNotNone(ModelService)
        self.assertIsNotNone(TrainingService)
        self.assertIsNotNone(InferenceService)

    def test_optimizers_exports(self):
        from core.optimizers import (
            create_core_optimizer,
            list_available_core_optimizers,
            CORE_OPTIMIZER_REGISTRY,
        )
        self.assertIsNotNone(create_core_optimizer)
        self.assertTrue(len(list_available_core_optimizers()) > 0)
        self.assertIn("extreme", CORE_OPTIMIZER_REGISTRY)

    def test_systems_exports(self):
        from core.systems import (
            DynamicFactory,
            EventEmitter,
            ServiceRegistry,
            PluginManager,
            ModuleLoader,
        )
        self.assertIsNotNone(DynamicFactory)
        self.assertIsNotNone(EventEmitter)
        self.assertIsNotNone(ServiceRegistry)
        self.assertIsNotNone(PluginManager)
        self.assertIsNotNone(ModuleLoader)

    def test_sys_modules_shims(self):
        import sys
        import core
        self.assertIn("optimization_core.core.ops", sys.modules)
        self.assertIn("optimization_core.core.util", sys.modules)
        self.assertIn("optimization_core.core.kernel", sys.modules)
        self.assertIn("optimization_core.core.optimizers", sys.modules)
        self.assertIn("optimization_core.core.services", sys.modules)

    # ---- New tests for the refactoring ----

    def test_kernels_backward_compat(self):
        """kernels/ should still be importable and re-export kernel components."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from core.kernels import TruthGPTKernel, KernelConfig, LogLevel
            self.assertIsNotNone(TruthGPTKernel)
            self.assertIsNotNone(KernelConfig)
            self.assertIsNotNone(LogLevel)

    def test_kernels_resolves_to_shim(self):
        """core.kernels should be registered in sys.modules."""
        import core
        self.assertIn("core.kernels", sys.modules)
        self.assertIn("optimization_core.core.kernels", sys.modules)

    def test_kernel_exports_kernel_components(self):
        """kernel/ should export all kernel orchestrator components."""
        from core.kernel import (
            TruthGPTKernel,
            KernelConfig,
            LogLevel,
            get_kernel,
            set_kernel,
            AdvancedServiceManager,
        )
        self.assertIsNotNone(TruthGPTKernel)
        self.assertIsNotNone(get_kernel)
        self.assertIsNotNone(set_kernel)
        self.assertIsNotNone(AdvancedServiceManager)

    def test_modern_truthgpt_has_F_import(self):
        """ModernTruthGPTOptimizer should have torch.nn.functional imported."""
        import core.optimizers.modern_truthgpt_optimizer as mod
        import torch.nn.functional
        # Verify the module has access to F
        self.assertTrue(hasattr(mod, 'F') or 'F' in dir(mod))

    def test_registry_module_paths_correct(self):
        """CORE_OPTIMIZER_REGISTRY module paths should be valid dotted paths."""
        from core.optimizers import CORE_OPTIMIZER_REGISTRY
        for name, entry in CORE_OPTIMIZER_REGISTRY.items():
            module_path = entry["module"]
            # All paths should start with "core."
            self.assertTrue(
                module_path.startswith("core."),
                f"Registry entry '{name}' has invalid module path: {module_path}"
            )
            # None should have bare module names without package prefix
            self.assertGreater(
                module_path.count("."), 1,
                f"Registry entry '{name}' module path is too shallow: {module_path}"
            )

    def test_distributed_optimizer_stubs(self):
        """DistributedOptimizer should raise NotImplementedError for unimplemented methods."""
        from core.distributed_runtime.distributed_optimizer import DistributedOptimizer
        opt = DistributedOptimizer(world_size=2, rank=0)
        self.assertTrue(opt.initialized)
        with self.assertRaises(NotImplementedError):
            opt.all_reduce(None)
        with self.assertRaises(NotImplementedError):
            opt.barrier()

    def test_realtime_optimizer_fallback(self):
        """RealtimeOptimizer should report fallback status correctly."""
        from core.runtime_fallback.realtime_optimizer import RealtimeOptimizer
        opt = RealtimeOptimizer(fallback_strategy="cpu_eager")
        self.assertTrue(opt.is_fallback_active())
        self.assertEqual(opt.get_strategy(), "cpu_eager")

    def test_performance_optimizer_summary(self):
        """PerformanceOptimizer should track applied optimizations."""
        from optimization.performance_optimizer import PerformanceOptimizer
        opt = PerformanceOptimizer()
        summary = opt.get_optimization_summary()
        self.assertIn("optimizations_applied", summary)
        self.assertEqual(summary["count"], 0)

    def test_register_shim_helper(self):
        """_register_shim should populate sys.modules under all three prefixes."""
        import core
        # The _register_shim helper is used during init; verify the result
        for sub in ["ops", "util", "framework", "systems", "kernel", "optimizers"]:
            for prefix in [f"{core.__name__}.{sub}", f"core.{sub}", f"optimization_core.core.{sub}"]:
                self.assertIn(prefix, sys.modules, f"Missing shim for {prefix}")


if __name__ == "__main__":
    unittest.main()
