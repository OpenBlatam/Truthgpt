from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import torch


class Backend(Enum):
    PYTORCH = "pytorch"
    RUST = "rust"
    CPP = "cpp"
    VLLM = "vllm"
    TENSORRT_LLM = "tensorrt_llm"
    AUTO = "auto"


class HardwareProfile(Enum):
    A100 = "a100"
    H100 = "h100"
    RTX4090 = "rtx4090"
    CPU_GENERIC = "cpu_generic"
    AUTO = "auto"


@dataclass
class InferenceConfig:
    max_batch_size: int = 8
    max_seq_length: int = 512
    use_amp: bool = True
    amp_dtype: torch.dtype = torch.float16
    backend: Backend = Backend.AUTO
    hardware_profile: HardwareProfile = HardwareProfile.AUTO
    use_kv_cache: bool = True
    use_rust_tokenizer: bool = True
    use_cpp_attention: bool = True
    kv_cache_max_gpu_memory_fraction: float = 0.85

    def validate(self) -> None:
        """Validate bounds and compatibility of configuration settings."""
        if self.max_batch_size <= 0:
            raise ValueError(f"max_batch_size must be positive, got {self.max_batch_size}")
        if self.max_seq_length <= 0:
            raise ValueError(f"max_seq_length must be positive, got {self.max_seq_length}")
        if not (0.0 < self.kv_cache_max_gpu_memory_fraction <= 1.0):
            raise ValueError(f"kv_cache_max_gpu_memory_fraction must be in (0.0, 1.0], got {self.kv_cache_max_gpu_memory_fraction}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary representation with type normalization."""
        return {
            "max_batch_size": self.max_batch_size,
            "max_seq_length": self.max_seq_length,
            "use_amp": self.use_amp,
            "amp_dtype": str(self.amp_dtype),
            "backend": self.backend.value if isinstance(self.backend, Backend) else str(self.backend),
            "hardware_profile": self.hardware_profile.value if isinstance(self.hardware_profile, HardwareProfile) else str(self.hardware_profile),
            "use_kv_cache": self.use_kv_cache,
            "use_rust_tokenizer": self.use_rust_tokenizer,
            "use_cpp_attention": self.use_cpp_attention,
            "kv_cache_max_gpu_memory_fraction": self.kv_cache_max_gpu_memory_fraction,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferenceConfig":
        """Instantiate InferenceConfig from dictionary with validation."""
        kwargs = dict(data)
        if "backend" in kwargs and isinstance(kwargs["backend"], str):
            kwargs["backend"] = Backend(kwargs["backend"])
        if "hardware_profile" in kwargs and isinstance(kwargs["hardware_profile"], str):
            kwargs["hardware_profile"] = HardwareProfile(kwargs["hardware_profile"])
        if "amp_dtype" in kwargs and isinstance(kwargs["amp_dtype"], str):
            kwargs["amp_dtype"] = getattr(torch, kwargs["amp_dtype"].replace("torch.", ""), torch.float16)
        config = cls(**kwargs)
        config.validate()
        return config


@dataclass
class GenerationConfig:
    max_new_tokens: int = 64
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True
    num_beams: int = 1

    def validate(self) -> None:
        """Validate hyperparameter limits."""
        if self.max_new_tokens <= 0:
            raise ValueError(f"max_new_tokens must be > 0, got {self.max_new_tokens}")
        if self.temperature < 0.0:
            raise ValueError(f"temperature must be >= 0.0, got {self.temperature}")
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError(f"top_p must be in [0.0, 1.0], got {self.top_p}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert generation configuration to dictionary representation."""
        return {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "do_sample": self.do_sample,
            "num_beams": self.num_beams,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationConfig":
        """Instantiate GenerationConfig from dictionary safely."""
        valid_keys = {
            "max_new_tokens", "temperature", "top_p", "top_k",
            "repetition_penalty", "do_sample", "num_beams"
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        config = cls(**filtered)
        config.validate()
        return config

    def to_pydantic(self) -> Any:
        """Convert to Pydantic GenerationConfig model."""
        try:
            from ..schemas.engine_configs import GenerationConfig as PydanticGenerationConfig
            return PydanticGenerationConfig(**self.to_dict())
        except ImportError:
            return self.to_dict()

    @classmethod
    def from_pydantic(cls, model: Any) -> "GenerationConfig":
        """Instantiate GenerationConfig from Pydantic model."""
        data = model.model_dump() if hasattr(model, "model_dump") else model.dict()
        return cls.from_dict(data)


