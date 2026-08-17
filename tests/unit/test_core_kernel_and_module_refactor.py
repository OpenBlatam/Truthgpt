"""
Unit test suite for optimization_core.core submodules and kernel refactoring.

Verifies:
- Core module listing and lazy imports for kernel, kernels, platform, lib, etc.
- core.kernel exports (TruthGPTKernel, KernelConfig, LogLevel, get_kernel, set_kernel)
- core.kernels compatibility shim and service exports (AgentService, BenchmarkService, TraceService, BaseService)
- sys.modules shims for backward compatibility
- Integration across core systems and optimizers
"""

import sys
import unittest
from pathlib import Path

# Add optimization_core directory to sys.path
opt_core_dir = str(Path(__file__).parent.parent.parent)
if opt_core_dir not in sys.path:
    sys.path.insert(0, opt_core_dir)

if "core" in sys.modules and not hasattr(sys.modules["core"], "list_available_core_modules"):
    del sys.modules["core"]


class TestCoreKernelAndModuleRefactor(unittest.TestCase):
    """Test suite for core kernel and submodule refactoring."""

    def test_core_submodules_registration(self):
        """Test that all core submodules are listed in list_available_core_modules()."""
        import core
        modules = core.list_available_core_modules()
        expected = [
            "systems",
            "optimizers",
            "ops",
            "util",
            "kernel",
            "kernels",
            "services",
            "adapters",
            "framework",
            "validation",
            "composition",
            "runtime",
            "common_runtime",
            "data",
            "platform",
            "lib",
            "distributed_runtime",
            "runtime_fallback",
        ]
        for mod in expected:
            self.assertIn(mod, modules)

    def test_core_kernel_exports(self):
        """Test core.kernel module imports and singleton accessors."""
        from core.kernel import (
            TruthGPTKernel,
            KernelConfig,
            LogLevel,
            HealthMonitor,
            PluginManager,
            AdvancedServiceManager,
            ProductionEventBus,
            get_kernel,
            set_kernel,
        )

        config = KernelConfig(log_level=LogLevel.INFO)
        self.assertEqual(config.log_level, LogLevel.INFO)

        kernel = TruthGPTKernel(config)
        self.assertIsNotNone(kernel)
        self.assertIsNotNone(kernel.service_manager)
        self.assertIsNotNone(kernel.event_bus)

        set_kernel(kernel)
        self.assertIs(get_kernel(), kernel)

    def test_core_kernels_shim_and_services(self):
        """Test core.kernels compatibility shim and kernel services."""
        from core.kernels import (
            TruthGPTKernel as ShimKernel,
            KernelConfig as ShimConfig,
            LogLevel as ShimLogLevel,
            AgentService,
            ModelService,
            ResearchService,
            OptimizationService,
            InferenceService,
            BenchmarkService,
            TraceService,
            BaseService,
        )

        self.assertIsNotNone(ShimKernel)
        self.assertIsNotNone(ShimConfig)
        self.assertIsNotNone(ShimLogLevel)
        self.assertIsNotNone(AgentService)
        self.assertIsNotNone(BenchmarkService)
        self.assertIsNotNone(TraceService)
        self.assertIsNotNone(BaseService)

    def test_sys_modules_shims(self):
        """Test that backward-compatibility sys.modules shims are loaded properly."""
        import core

        self.assertIn("optimization_core.core.kernel", sys.modules)
        self.assertIn("optimization_core.core.kernels", sys.modules)
        self.assertIn("optimization_core.core.dynamic_factory", sys.modules)
        self.assertIn("optimization_core.core.event_system", sys.modules)
        self.assertIn("optimization_core.core.service_registry", sys.modules)

    def test_lazy_imports_submodules(self):
        """Test lazy loading of core submodules via attribute access."""
        import core

        self.assertIsNotNone(core.kernel)
        self.assertIsNotNone(core.kernels)
        self.assertIsNotNone(core.platform)
        self.assertIsNotNone(core.lib)
        self.assertIsNotNone(core.distributed_runtime)
        self.assertIsNotNone(core.runtime_fallback)


if __name__ == "__main__":
    unittest.main()
