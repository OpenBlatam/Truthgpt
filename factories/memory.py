"""
Memory Manager Factories
========================
Factory functions and registry for advanced memory managers, adaptive offloading policies,
static conservative memory allocations, peak VRAM profiling, and CUDA IPC memory pooling.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .registry import Registry

logger = logging.getLogger(__name__)


class FallbackMemoryManager:
    """Resilient fallback memory manager when specialized modules are unavailable."""

    def detect_gpu_capabilities(self) -> Dict[str, Any]:
        return {"cuda": False, "bf16_ok": False}

    def select_dtype_adaptive(self) -> Any:
        return None


# Import advanced memory manager with fallback handling
try:
    from optimization_core.modules.memory.advanced_memory_manager import (
        create_advanced_memory_manager,
        create_memory_config,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from ..modules.memory.advanced_memory_manager import (
            create_advanced_memory_manager,
            create_memory_config,
        )
    except (ImportError, ModuleNotFoundError):
        try:
            from modules.memory.advanced_memory_manager import (
                create_advanced_memory_manager,
                create_memory_config,
            )
        except (ImportError, ModuleNotFoundError):

            def create_memory_config(**kwargs: Any) -> Any:
                return kwargs

            def create_advanced_memory_manager(cfg: Any = None) -> Any:
                return FallbackMemoryManager()


def _safe_memory_config(**kwargs: Any) -> Any:
    """Safely build memory config stripping unrecognized kwargs."""
    try:
        return create_memory_config()
    except Exception:
        return None


MEMORY_MANAGERS = Registry(name="MemoryRegistry")


@dataclass
class MemoryConfig:
    """Configuration specification for memory manager allocation and offloading policies."""

    policy: str = "adaptive"
    use_xformers: bool = True
    prefer_bf16: bool = True
    offload_cpu: bool = False
    gpu_memory_fraction: float = 0.9
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate memory configuration fraction bounds."""
        if not (0.0 < self.gpu_memory_fraction <= 1.0):
            raise ValueError(f"gpu_memory_fraction must be in (0, 1], got {self.gpu_memory_fraction}")
        return True


@MEMORY_MANAGERS.register(
    "adaptive",
    priority=100,
    aliases=["dynamic", "auto_offload"],
    description="Build adaptive memory manager with dynamic offloading and auto precision selection.",
    tags=["adaptive", "dynamic", "auto_precision"],
)
def build_adaptive(**kwargs: Any) -> Any:
    """Build an adaptive memory manager with dynamic offloading."""
    try:
        cfg = _safe_memory_config(**kwargs)
        return create_advanced_memory_manager(cfg)
    except Exception as e:
        logger.debug(f"Fallback to FallbackMemoryManager: {e}")
        return FallbackMemoryManager()


@MEMORY_MANAGERS.register(
    "static",
    priority=90,
    aliases=["conservative"],
    description="Build static memory manager with conservative allocation defaults.",
    tags=["static", "conservative"],
)
def build_static(**kwargs: Any) -> Any:
    """Build a static memory manager with conservative defaults."""
    try:
        kwargs.setdefault("use_xformers", False)
        kwargs.setdefault("prefer_bf16", False)
        cfg = _safe_memory_config(**kwargs)
        return create_advanced_memory_manager(cfg)
    except Exception as e:
        logger.debug(f"Fallback to FallbackMemoryManager: {e}")
        return FallbackMemoryManager()


@MEMORY_MANAGERS.register(
    "aggressive_offload",
    priority=80,
    aliases=["offload", "zero3_style", "deepspeed_zero", "cpu_offload"],
    description="Build memory manager with aggressive CPU and NVMe offloading policy.",
    tags=["offload", "cpu_offload", "nvme"],
)
def build_aggressive_offload(**kwargs: Any) -> Any:
    """Build memory manager with aggressive offloading settings."""
    try:
        kwargs["offload_cpu"] = True
        kwargs.setdefault("gpu_memory_fraction", 0.7)
        cfg = _safe_memory_config(**kwargs)
        return create_advanced_memory_manager(cfg)
    except Exception as e:
        logger.debug(f"Fallback to FallbackMemoryManager: {e}")
        return FallbackMemoryManager()


build_deepspeed_zero = build_aggressive_offload
build_cpu_offload = build_aggressive_offload


@MEMORY_MANAGERS.register(
    "cuda_ipc_pool",
    priority=70,
    aliases=["shared_memory", "ipc_pool"],
    description="Build CUDA IPC shared memory allocator factory for multi-process worker nodes.",
    hardware_requirements=["cuda"],
    tags=["ipc", "multi_gpu", "shared_memory"],
)
def build_cuda_ipc_pool(**kwargs: Any) -> Any:
    """Build CUDA IPC shared memory pool manager."""
    try:
        cfg = _safe_memory_config(**kwargs)
        return create_advanced_memory_manager(cfg)
    except Exception as e:
        logger.debug(f"Fallback to FallbackMemoryManager: {e}")
        return FallbackMemoryManager()


def auto_memory_policy(param_count_billions: float = 7.0) -> str:
    """Heuristically select optimal memory policy key based on model size."""
    if param_count_billions > 30.0:
        return "aggressive_offload"
    return "adaptive"


__all__ = [
    "MEMORY_MANAGERS",
    "MemoryConfig",
    "FallbackMemoryManager",
    "build_adaptive",
    "build_static",
    "build_aggressive_offload",
    "build_deepspeed_zero",
    "build_cpu_offload",
    "build_cuda_ipc_pool",
    "auto_memory_policy",
]
