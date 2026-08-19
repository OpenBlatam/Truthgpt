"""
Base Utility Classes and Hardware Telemetry Helpers for Optimization Core.
==========================================================================
Provides foundational abstractions, Pydantic model bases, and unified CUDA/CPU/MPS
resource management for the entire optimization_core subsystem.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
from pydantic import BaseModel, ConfigDict

try:
    from .interfaces import BaseHardwareManager
    from .types import HardwareDevice, HardwareInfo
except (ImportError, ValueError):
    try:
        from interfaces import BaseHardwareManager
        from types import HardwareDevice, HardwareInfo
    except (ImportError, ValueError):
        from utils.interfaces import BaseHardwareManager
        from utils.types import HardwareDevice, HardwareInfo



logger = logging.getLogger(__name__)


class BaseOptimizationModel(BaseModel):
    """
    Base Pydantic model for all optimization configurations, schemas, and results.
    Standardizes settings like arbitrary type allowance and provides serializable summaries.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='ignore'
    )

    def to_summary(self) -> Dict[str, Any]:
        """Returns a simplified dictionary summary of the model."""
        return self.model_dump(exclude_none=True)

    def to_dict(self) -> Dict[str, Any]:
        """Export full model attributes to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseOptimizationModel:
        """Instantiate model from dictionary."""
        return cls(**data)


class CudaResourceManager(BaseHardwareManager):
    """
    Helper for standardized CUDA/GPU/CPU resource management (streams, memory, synchronization).
    Reduces boilerplate in classes that require parallel GPU processing and hardware telemetry.
    """

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize CUDA resource telemetry."""
        pass

    def shutdown(self) -> None:
        """Synchronize and empty accelerator caches on shutdown."""
        self.synchronize()
        self.empty_cache()

    def health_check(self) -> Dict[str, Any]:
        """Perform hardware health check."""
        info = self.get_device_info()
        return {
            "status": "healthy",
            "device": info.get("device", "cpu"),
            "available": info.get("available", False),
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Return resource manager metadata."""
        return {
            "name": "CudaResourceManager",
            "category": "hardware",
            "version": "2.0.0",
        }

    @staticmethod
    def get_streams(num_streams: int, enabled: bool = True) -> Optional[List[torch.cuda.Stream]]:
        """
        Safely initialize a list of CUDA streams.

        Args:
            num_streams: Number of streams to create.
            enabled: Whether streams are actually requested.

        Returns:
            List of torch.cuda.Stream objects or None if not available/requested.
        """
        if enabled and torch.cuda.is_available():
            try:
                return [torch.cuda.Stream() for _ in range(num_streams)]
            except Exception as e:
                logger.warning(f"Failed to initialize CUDA streams: {e}")
                return None
        return None

    @staticmethod
    def get_device_info() -> Dict[str, Any]:
        """Returns a standardized dictionary of current device specifications and memory."""
        info: Dict[str, Any] = {"device": "cpu", "available": False}
        if torch.cuda.is_available():
            try:
                info.update({
                    "device": "cuda",
                    "available": True,
                    "count": torch.cuda.device_count(),
                    "name": torch.cuda.get_device_name(0),
                    "memory_allocated_mb": round(torch.cuda.memory_allocated() / (1024 * 1024), 2),
                    "memory_reserved_mb": round(torch.cuda.memory_reserved() / (1024 * 1024), 2),
                    "max_memory_allocated_mb": round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2),
                })
            except Exception as e:
                logger.warning(f"Error querying CUDA device info: {e}")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            info.update({
                "device": "mps",
                "available": True,
                "count": 1,
                "name": "Apple Silicon MPS",
            })
        return info

    @staticmethod
    def get_typed_device_info() -> HardwareInfo:
        """Returns strongly-typed HardwareInfo schema."""
        raw = CudaResourceManager.get_device_info()
        dev_enum = HardwareDevice(raw["device"]) if raw["device"] in HardwareDevice.__members__.values() else HardwareDevice.CPU
        return HardwareInfo(
            device=dev_enum,
            available=raw.get("available", False),
            device_count=raw.get("count", 0),
            name=raw.get("name", "CPU"),
            allocated_memory_mb=raw.get("memory_allocated_mb", 0.0),
            reserved_memory_mb=raw.get("memory_reserved_mb", 0.0),
        )

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Collect current system and GPU memory metrics."""
        return system_metrics_collector()

    @staticmethod
    def synchronize() -> None:
        """Synchronize active CUDA stream."""
        if torch.cuda.is_available():
            try:
                torch.cuda.synchronize()
            except Exception as e:
                logger.warning(f"CUDA synchronization failed: {e}")

    @staticmethod
    def empty_cache() -> None:
        """Clear cached allocations from the GPU memory pool."""
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"CUDA empty_cache failed: {e}")


def system_metrics_collector() -> Dict[str, float]:
    """
    Helper function to collect standardized system and GPU metrics.
    Gracefully handles absence of psutil or CUDA.
    """
    metrics = {
        "timestamp": time.time(),
        "cpu_percent": 0.0,
        "memory_used_gb": 0.0,
        "gpu_used_mb": 0.0,
    }

    try:
        import psutil
        metrics["cpu_percent"] = psutil.cpu_percent()
        metrics["memory_used_gb"] = round(psutil.virtual_memory().used / (1024**3), 3)
    except ImportError:
        pass

    if torch.cuda.is_available():
        try:
            metrics["gpu_used_mb"] = round(torch.cuda.memory_allocated() / (1024**2), 2)
        except Exception:
            pass

    return metrics
