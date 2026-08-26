"""
Kernel Infrastructure Services Sub-package.
"""

from .resource_manager import (
    ResourceManager,
    ResourceRequirements,
    GPUInfo,
    ResourceAllocation,
)

__all__ = [
    "ResourceManager",
    "ResourceRequirements",
    "GPUInfo",
    "ResourceAllocation",
]
