"""
TruthGPT Kernel Package

Provides the core kernel architecture for TruthGPT:
- TruthGPTKernel: Main kernel orchestrator
- KernelConfig: Kernel configuration dataclass
- KernelState: Kernel lifecycle states
- get_kernel(): Global kernel singleton accessor
- set_kernel(): Global kernel singleton setter

Usage:
    from truthgpt.core.kernels import get_kernel, TruthGPTKernel, KernelConfig

    config = KernelConfig(
        log_level="INFO",
        enable_hot_reload=True,
        max_concurrent_tasks=1000,
    )
    kernel = TruthGPTKernel(config)
    await kernel.run()
"""

from .truthgpt_kernel import (
    TruthGPTKernel,
    KernelConfig,
    KernelState,
    get_kernel,
    set_kernel,
)

from .services import (
    AgentService,
    ModelService,
    ResearchService,
    OptimizationService,
    InferenceService,
)

__all__ = [
    # Kernel core
    "TruthGPTKernel",
    "KernelConfig",
    "KernelState",
    "get_kernel",
    "set_kernel",
    # Services
    "AgentService",
    "ModelService",
    "ResearchService",
    "OptimizationService",
    "InferenceService",
]
