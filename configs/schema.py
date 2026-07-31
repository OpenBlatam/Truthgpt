"""Unified configuration schema module for Optimization Core (Canonical configs package).

Provides enterprise-grade Pydantic v2 validation models for model metadata,
neural training parameters, high-performance inference, and kernel optimizations.
"""

import sys
import json
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["config.schema"] = _mod
    sys.modules["configurations.schema"] = _mod
    sys.modules["optimization_core.configs.schema"] = _mod


class BaseOptimizationSchema(BaseModel):
    """Base schema with standard serialization and validation config."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration model to a standard python dictionary."""
        return self.model_dump()

    def to_json(self, **kwargs: Any) -> str:
        """Serialize configuration model to JSON string."""
        return json.dumps(self.to_dict(), default=str, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseOptimizationSchema":
        """Instantiate configuration model from dictionary with type coercion."""
        return cls.model_validate(data)


class QuantizationCfg(BaseOptimizationSchema):
    """Configuration model for model weight & activation quantization."""
    enabled: bool = Field(default=False, description="Enable quantization pass")
    mode: str = Field(default="int8", description="Quantization mode (fp16, int8, int4, fp8)")
    per_channel: bool = Field(default=True, description="Enable per-channel quantization scaling")
    symmetric: bool = Field(default=True, description="Use symmetric quantization range")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = {"fp16", "int8", "int4", "fp8", "none"}
        if v.lower() not in allowed:
            raise ValueError(f"Quantization mode must be one of {allowed}, got '{v}'")
        return v.lower()


class KVCacheCfg(BaseOptimizationSchema):
    """Configuration model for attention Key-Value cache management."""
    enabled: bool = Field(default=True, description="Enable key-value caching optimization")
    max_cache_size: int = Field(default=4096, ge=128, description="Maximum cached token sequence length")
    paged_attention: bool = Field(default=True, description="Use non-contiguous paged memory management")
    quantize_kv: bool = Field(default=False, description="Enable KV cache int8 quantization")


class CompilerCfg(BaseOptimizationSchema):
    """Configuration for TorchDynamo and JIT compilers."""
    enable_dynamo: bool = Field(default=True, description="Enable PyTorch 2.0 Dynamo compilation")
    backend: str = Field(default="inductor", description="TorchDynamo compiler backend engine")
    mode: str = Field(default="default", description="Compilation mode (default, reduce-overhead, max-autotune)")
    fullgraph: bool = Field(default=False, description="Require full graph capture without graph breaks")


class AgentOrchestratorCfg(BaseOptimizationSchema):
    """Configuration for multi-agent persistence and task coordination."""
    max_workers: int = Field(default=4, ge=1, description="Maximum concurrent worker threads/tasks")
    db_path: str = Field(default="agent_persistence.db", description="SQLite database path for state persistence")
    timeout_seconds: float = Field(default=60.0, gt=0.0, description="Execution timeout per agent step")


class TrainingCfg(BaseOptimizationSchema):
    """Configuration model for neural network training parameters."""
    epochs: int = Field(default=3, ge=1, description="Number of training epochs")
    train_batch_size: int = Field(default=8, ge=1, description="Per-device training batch size")
    eval_batch_size: int = Field(default=8, ge=1, description="Per-device evaluation batch size")
    grad_accum_steps: int = Field(default=2, ge=1, description="Gradient accumulation steps")
    learning_rate: float = Field(default=5e-5, gt=0, description="Peak learning rate")
    warmup_ratio: float = Field(default=0.06, ge=0, le=1, description="Warmup ratio for scheduler")
    mixed_precision: str = Field(default="bf16", description="Mixed precision mode (no|fp16|bf16)")

    @field_validator("mixed_precision")
    @classmethod
    def validate_precision(cls, v: str) -> str:
        allowed = {"no", "fp16", "bf16", "fp32", "int8", "int4"}
        if v.lower() not in allowed:
            raise ValueError(f"mixed_precision must be one of {allowed}, got '{v}'")
        return v.lower()


class ModelCfg(BaseOptimizationSchema):
    """Configuration model for model architecture and weights metadata."""
    family: str = Field(default="unknown", description="Model family identifier")
    name_or_path: str = Field(default="gpt2", description="HuggingFace model hub path or directory")
    torch_dtype: Optional[str] = Field(default=None, description="Torch tensor floating point precision")
    device_map: str = Field(default="auto", description="Device placement strategy")


class InferenceCfg(BaseOptimizationSchema):
    """Configuration model for high-performance inference engine."""
    max_tokens: int = Field(default=2048, ge=1, description="Maximum generation tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p nucleus sampling probability")
    kv_cache: KVCacheCfg = Field(default_factory=KVCacheCfg, description="KV cache configuration")

    @property
    def use_kv_cache(self) -> bool:
        """Backward compatibility property for KV cache activation flag."""
        return self.kv_cache.enabled


class OptimizationCfg(BaseOptimizationSchema):
    """Configuration model for engine optimization passes."""
    compiler: CompilerCfg = Field(default_factory=CompilerCfg, description="Compiler optimization settings")
    quantization: QuantizationCfg = Field(default_factory=QuantizationCfg, description="Quantization settings")
    enable_flash_attention: bool = Field(default=True, description="Enable FlashAttention kernel optimizations")

    @property
    def enable_dynamo(self) -> bool:
        """Backward compatibility property for TorchDynamo status."""
        return self.compiler.enable_dynamo

    @property
    def quantization_level(self) -> str:
        """Backward compatibility property for quantization mode."""
        return self.quantization.mode


class AppCfg(BaseOptimizationSchema):
    """Top-level unified application configuration schema."""
    run_name: str = Field(default="run", description="Name identifier for current experiment run")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    model: ModelCfg = Field(default_factory=ModelCfg, description="Model configuration settings")
    training: TrainingCfg = Field(default_factory=TrainingCfg, description="Training configuration settings")
    inference: InferenceCfg = Field(default_factory=InferenceCfg, description="Inference configuration settings")
    optimization: OptimizationCfg = Field(default_factory=OptimizationCfg, description="Optimization configuration settings")
    agent: AgentOrchestratorCfg = Field(default_factory=AgentOrchestratorCfg, description="Agent orchestrator configuration")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional dataset pipeline settings")


__all__ = [
    "BaseOptimizationSchema",
    "QuantizationCfg",
    "KVCacheCfg",
    "CompilerCfg",
    "AgentOrchestratorCfg",
    "TrainingCfg",
    "ModelCfg",
    "InferenceCfg",
    "OptimizationCfg",
    "AppCfg",
    "SystemCfg",
]

SystemCfg = AppCfg


