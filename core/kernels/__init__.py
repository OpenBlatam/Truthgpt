"""
TruthGPT Kernel Package & Services Shim.

DEPRECATED: This module exists for backward compatibility.
Use `core.kernel` directly for kernel components.
Use `core.kernel.services` or import kernel services from `core.kernel`.

Provides backward-compatible access to the core kernel and kernel services:
- TruthGPTKernel: Main kernel orchestrator (from core.kernel)
- KernelConfig, LogLevel: Configuration data structures (from core.kernel)
- get_kernel, set_kernel: Singleton accessors (from core.kernel)
- Kernel services: AgentService, ModelService, ResearchService, etc.
"""

import warnings as _warnings

# Flag set by core/__init__.py to suppress this warning during package init.
_SUPPRESS_DEPRECATION = False

if not _SUPPRESS_DEPRECATION:
    _warnings.warn(
        "core.kernels is deprecated, use core.kernel instead",
        DeprecationWarning,
        stacklevel=2,
    )

from ..kernel import (
    TruthGPTKernel,
    KernelConfig,
    LogLevel,
    get_kernel,
    set_kernel,
)

from .services import (
    AgentService,
    ModelService,
    ResearchService,
    OptimizationService,
    InferenceService,
    BenchmarkService,
    TraceService,
    BaseService,
)

__all__ = [
    # Kernel core
    "TruthGPTKernel",
    "KernelConfig",
    "LogLevel",
    "get_kernel",
    "set_kernel",
    # Services
    "AgentService",
    "ModelService",
    "ResearchService",
    "OptimizationService",
    "InferenceService",
    "BenchmarkService",
    "TraceService",
    "BaseService",
]
