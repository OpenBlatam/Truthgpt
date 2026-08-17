"""
TruthGPT Core Kernel Submodule.

Provides core kernel orchestrator, configuration, event bus, and service management:
- TruthGPTKernel: Main kernel orchestrator
- KernelConfig, ServiceConfig, LogLevel: Configuration data structures and enums
- HealthMonitor, PluginManager: Core kernel components
- AdvancedServiceManager: Enterprise service manager
- ProductionEventBus: Production event bus

Also re-exports TruthGPT Kernel Services (formerly in core.kernels.services):
- AgentService, ModelService, ResearchService, OptimizationService,
  InferenceService, BenchmarkService, TraceService
"""

from .truthgpt_kernel import (
    TruthGPTKernel,
    HealthMonitor,
    PluginManager,
)

from .config.kernel_config import (
    KernelConfig,
    ServiceConfig,
    MonitoringConfig,
    EventBusConfig,
    CLIConfig,
    PluginConfig,
    LogLevel,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    TESTING_CONFIG,
)

from .services.advanced_service_manager import AdvancedServiceManager
from .events.production_event_bus import ProductionEventBus

# Global singleton accessors
_GLOBAL_KERNEL_INSTANCE = None


def get_kernel() -> TruthGPTKernel:
    """Get global kernel instance."""
    global _GLOBAL_KERNEL_INSTANCE
    if _GLOBAL_KERNEL_INSTANCE is None:
        _GLOBAL_KERNEL_INSTANCE = TruthGPTKernel()
    return _GLOBAL_KERNEL_INSTANCE


def set_kernel(kernel: TruthGPTKernel) -> None:
    """Set global kernel instance."""
    global _GLOBAL_KERNEL_INSTANCE
    _GLOBAL_KERNEL_INSTANCE = kernel


__all__ = [
    # Kernel Orchestrator & Components
    "TruthGPTKernel",
    "HealthMonitor",
    "PluginManager",
    # Configuration
    "KernelConfig",
    "ServiceConfig",
    "MonitoringConfig",
    "EventBusConfig",
    "CLIConfig",
    "PluginConfig",
    "LogLevel",
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG",
    "TESTING_CONFIG",
    # Infrastructure
    "AdvancedServiceManager",
    "ProductionEventBus",
    # Singleton Accessors
    "get_kernel",
    "set_kernel",
]

