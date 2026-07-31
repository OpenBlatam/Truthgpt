import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class PyTorchOptimizationLevel(Enum):
    """PyTorch-inspired optimization levels."""
    BASIC = "basic"           # Standard PyTorch optimizations
    ADVANCED = "advanced"     # Advanced PyTorch optimizations
    EXPERT = "expert"         # Expert-level optimizations
    MASTER = "master"         # Master-level optimizations
    LEGENDARY = "legendary"   # Legendary PyTorch optimizations

@dataclass
class PyTorchOptimizationResult:
    """Result of PyTorch-inspired optimization."""
    optimized_model: nn.Module
    speed_improvement: float
    memory_reduction: float
    accuracy_preservation: float
    energy_efficiency: float
    optimization_time: float
    level: PyTorchOptimizationLevel
    techniques_applied: List[str]
    performance_metrics: Dict[str, float]
    pytorch_compatibility: float = 0.0
    inductor_optimization: float = 0.0
    dynamo_optimization: float = 0.0
    quantization_benefit: float = 0.0
    distributed_benefit: float = 0.0

    def get_composite_score(self) -> float:
        """Calculate weighted efficiency score combining speedup, memory, and accuracy."""
        return (
            0.4 * self.speed_improvement +
            0.3 * self.memory_reduction +
            0.2 * self.accuracy_preservation +
            0.1 * self.energy_efficiency
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable summary dictionary excluding torch nn.Module weights."""
        return {
            "speed_improvement": self.speed_improvement,
            "memory_reduction": self.memory_reduction,
            "accuracy_preservation": self.accuracy_preservation,
            "energy_efficiency": self.energy_efficiency,
            "optimization_time": self.optimization_time,
            "level": self.level.value if isinstance(self.level, PyTorchOptimizationLevel) else str(self.level),
            "techniques_applied": self.techniques_applied,
            "performance_metrics": self.performance_metrics,
            "composite_score": self.get_composite_score(),
            "pytorch_compatibility": self.pytorch_compatibility,
            "inductor_optimization": self.inductor_optimization,
            "dynamo_optimization": self.dynamo_optimization,
            "quantization_benefit": self.quantization_benefit,
            "distributed_benefit": self.distributed_benefit,
        }


def create_model_summary(model: nn.Module) -> Dict[str, Any]:
    """Calculate parameter counts, trainable weights, and memory usage for a PyTorch module."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    size_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    
    return {
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "non_trainable_parameters": total_params - trainable_params,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }


__all__ = [
    "PyTorchOptimizationLevel",
    "PyTorchOptimizationResult",
    "create_model_summary",
]


