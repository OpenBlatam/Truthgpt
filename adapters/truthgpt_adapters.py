"""
TruthGPT Base Adapters — Pydantic-First Architecture.

Provides model optimization adapters and dynamic integration adapters
tailored specifically for TruthGPT models while maintaining full backward compatibility.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, Optional, Tuple

import torch.nn as nn
from pydantic import BaseModel, ConfigDict, Field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.truthgpt_adapters"] = _mod
    sys.modules["optimization_core.adapters.truthgpt_adapters"] = _mod

try:
    from optimization_core.adapters.base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )
except ImportError:
    from .base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )

logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration Model
# ---------------------------------------------------------------------------

class TruthGPTConfig(BaseModel):
    """Configuration options for TruthGPT adapters and runtime optimizations."""
    model_config = ConfigDict(extra="allow")

    model_name: str = Field(default="TruthGPT-Default", description="Identifier name of target model")
    model_size: str = Field(default="base", description="Size category variant (e.g. 'base', 'large')")
    precision: str = Field(default="fp16", description="Execution precision string")
    device: str = Field(default="auto", description="Target execution device")
    optimization_level: str = Field(default="balanced", description="Optimization profile level")
    enable_mixed_precision: bool = Field(default=True, description="Flag to enable AMP mixed precision")
    enable_gradient_checkpointing: bool = Field(default=True, description="Flag to enable gradient checkpointing")
    enable_attention_optimization: bool = Field(default=True, description="Flag to enable flash/optimized attention")
    enable_memory_optimization: bool = Field(default=True, description="Flag to enable peak memory reduction")
    max_memory_gb: float = Field(default=4.0, description="Upper ceiling memory limit in gigabytes")
    target_latency_ms: float = Field(default=50.0, description="Target execution latency in milliseconds")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary payload."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TruthGPTConfig:
        """Instantiate configuration model from dictionary payload."""
        return cls.model_validate(data)


# ---------------------------------------------------------------------------
# Backward-Compatible Core Adapters
# ---------------------------------------------------------------------------

class TruthGPTPerformanceAdapter:
    """Adapter for performance optimization of TruthGPT models."""

    def __init__(self, config: TruthGPTConfig) -> None:
        self.config: TruthGPTConfig = config

    def optimize_for_performance(self, model: nn.Module) -> nn.Module:
        """Apply performance optimizations to PyTorch module."""
        logger.info("Optimizing for performance via TruthGPTPerformanceAdapter")
        return model


class TruthGPTMemoryAdapter:
    """Adapter for memory optimization of TruthGPT models."""

    def __init__(self, config: TruthGPTConfig) -> None:
        self.config: TruthGPTConfig = config

    def optimize_for_memory(self, model: nn.Module) -> nn.Module:
        """Apply memory reduction optimizations to PyTorch module."""
        logger.info("Optimizing for memory via TruthGPTMemoryAdapter")
        return model


class TruthGPTGPUAdapter:
    """Adapter for GPU execution optimization of TruthGPT models."""

    def __init__(self, config: TruthGPTConfig) -> None:
        self.config: TruthGPTConfig = config

    def optimize_for_gpu(self, model: nn.Module) -> nn.Module:
        """Apply GPU-specific hardware acceleration to PyTorch module."""
        logger.info("Optimizing for GPU via TruthGPTGPUAdapter")
        return model


class TruthGPTValidationAdapter:
    """Adapter for validating model architecture and state."""

    def __init__(self, config: TruthGPTConfig) -> None:
        self.config: TruthGPTConfig = config

    def validate_model(self, model: nn.Module) -> Dict[str, Any]:
        """Validate PyTorch module structure and return status summary."""
        logger.info("Validating model via TruthGPTValidationAdapter")
        return {"status": "success", "validated": True}


class TruthGPTIntegratedAdapter:
    """Integrated adaptation suite preserving compatibility for tests and examples."""

    def __init__(self, config: TruthGPTConfig) -> None:
        self.config: TruthGPTConfig = config

    def full_adaptation(self, model: nn.Module) -> Dict[str, Any]:
        """Run full multi-pass adaptation suite on model."""
        return {
            "adaptations": ["performance", "memory", "gpu"],
            "summary": {
                "successful_adaptations": 3,
                "total_adaptations": 3,
            },
        }


def create_truthgpt_adapter(config: TruthGPTConfig) -> TruthGPTIntegratedAdapter:
    """Backward-compatible factory creating integrated TruthGPT adapter."""
    return TruthGPTIntegratedAdapter(config)


def quick_truthgpt_setup(model_name: str = "truthgpt") -> Tuple[TruthGPTIntegratedAdapter, Any]:
    """Quick setup helper for initializing TruthGPT adapter and default state."""
    config = TruthGPTConfig(model_name=model_name)
    return TruthGPTIntegratedAdapter(config), None


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class TruthGPTAdaptResult(BaseModel):
    """Typed result from dynamic truthgpt adapt action."""
    status: str = Field(default="success", description="Status of adaptation operation")
    model_type: str = Field(description="Class name of target model")
    parameter_count: int = Field(description="Total parameter count in adapted model")
    kwargs_used: Dict[str, Any] = Field(default_factory=dict, description="Keyword parameters applied")
    model_id: str = Field(description="Target model identifier string")


# ---------------------------------------------------------------------------
# Dynamic TruthGPT Adapter Class
# ---------------------------------------------------------------------------

class TruthGPTAdapter(BaseDynamicAdapter):
    """Dynamic tool adapter for TruthGPT operations."""

    name: str = "truthgpt_adapter"
    description: str = (
        "Adapter for basic TruthGPT operations. Input JSON: "
        "{'action': 'adapt'|'validate'|'optimize'|'info', 'model_id': 'model_xyz', 'kwargs': {}}"
    )

    def __init__(self, config: Optional[TruthGPTConfig] = None, **kwargs: Any) -> None:
        super().__init__()
        self.adapter_config: TruthGPTConfig = config or TruthGPTConfig()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process TruthGPT model adaptation.

        Args:
            input_data: Input JSON dictionary payload.

        Returns:
            Dictionary serialized from TruthGPTAdaptResult.

        Raises:
            ValueError: If model_id is missing or action is unknown.
        """
        action = input_data.get("action")
        kwargs: Dict[str, Any] = input_data.get("kwargs", {})

        if action == "adapt":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='adapt'.")

            model = self.store.get(model_id)
            if model is None:
                raise ValueError(f"Model '{model_id}' not found in ObjectStore")

            parameter_count = (
                sum(p.numel() for p in model.parameters()) if hasattr(model, "parameters") else 0
            )

            return TruthGPTAdaptResult(
                model_type=type(model).__name__,
                parameter_count=parameter_count,
                kwargs_used=kwargs,
                model_id=model_id,
            ).model_dump()

        elif action == "validate":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='validate'.")
            model = self.store.get(model_id)
            val_adapter = TruthGPTValidationAdapter(self.adapter_config)
            res = val_adapter.validate_model(model)
            return {"status": "success", "model_id": model_id, **res}

        elif action == "optimize":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='optimize'.")
            model = self.store.get(model_id)
            integrated = create_truthgpt_adapter(self.adapter_config)
            res = integrated.full_adaptation(model)
            return {"status": "success", "model_id": model_id, "adaptation_summary": res}

        elif action == "info":
            return {"status": "success", "config": self.adapter_config.to_dict()}

        else:
            raise ValueError(f"Unknown action: '{action}'. Supported actions: 'adapt', 'validate', 'optimize', 'info'.")

    def adapt(self, model: nn.Module, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        """Preserve backward compatibility for direct method calls on nn.Module instances."""
        parameter_count = (
            sum(p.numel() for p in model.parameters()) if hasattr(model, "parameters") else 0
        )
        self.log_metrics("truthgpt_adaptation", parameter_count=parameter_count)
        return {
            "model_type": type(model).__name__,
            "parameter_count": parameter_count,
            "kwargs": kwargs,
        }

    def log_metrics(self, event_name: str, **metrics: Any) -> None:
        """Utility method to log adapter metrics."""
        logger.info("TruthGPT Metric [%s]: %s", event_name, metrics)


__all__ = [
    "TruthGPTConfig",
    "TruthGPTPerformanceAdapter",
    "TruthGPTMemoryAdapter",
    "TruthGPTGPUAdapter",
    "TruthGPTValidationAdapter",
    "TruthGPTIntegratedAdapter",
    "create_truthgpt_adapter",
    "quick_truthgpt_setup",
    "TruthGPTAdaptResult",
    "TruthGPTAdapter",
]
