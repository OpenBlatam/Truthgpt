"""
Type definitions, enums, dataclasses, and configuration schemas for models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import torch


class ModelArchitectureType(str, Enum):
    """Supported model architecture classes."""
    CAUSAL_LM = "causal_lm"
    SEQ2SEQ = "seq2seq"
    DIFFUSION = "diffusion"
    VISION_LANGUAGE = "vision_language"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    CUSTOM = "custom"


class PrecisionType(str, Enum):
    """Supported floating-point precision levels."""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"
    AUTO = "auto"

    @classmethod
    def to_torch_dtype(cls, precision: Union[str, "PrecisionType"]) -> Optional[torch.dtype]:
        """Convert precision string or enum to torch.dtype."""
        p = str(precision).lower()
        if p in ("fp32", "float32", "32", "precisiontype.fp32"):
            return torch.float32
        elif p in ("fp16", "float16", "16", "precisiontype.fp16"):
            return torch.float16
        elif p in ("bf16", "bfloat16", "precisiontype.bf16"):
            return torch.bfloat16
        return None


class DeviceMapType(str, Enum):
    """Device mapping placement strategies."""
    AUTO = "auto"
    BALANCED = "balanced"
    BALANCED_LOW_0 = "balanced_low_0"
    SEQUENTIAL = "sequential"
    CPU = "cpu"
    CUDA = "cuda"


class AttentionBackend(str, Enum):
    """Supported attention implementation backends."""
    AUTO = "auto"
    FLASH_ATTENTION = "flash"
    SDPA = "sdpa"
    XFORMERS = "xformers"
    TORCH = "torch"


class SchedulerType(str, Enum):
    """Supported diffusion noise schedulers."""
    DDIM = "ddim"
    DPM = "dpm"
    EULER = "euler"
    EULER_A = "euler_a"
    LMS = "lms"
    PNDM = "pndm"
    HEUN = "heun"


class QuantizationType(str, Enum):
    """Supported weight quantization formats."""
    NONE = "none"
    BITS_8 = "8bit"
    BITS_4 = "4bit"
    NF4 = "nf4"
    FP4 = "fp4"
    AWQ = "awq"
    GPTQ = "gptq"


@dataclass
class GenerationConfig:
    """
    Configuration parameters for text generation.
    """
    max_new_tokens: int = 64
    min_new_tokens: int = 0
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True
    num_return_sequences: int = 1
    pad_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    stop_strings: Optional[List[str]] = None
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        d = {
            "max_new_tokens": self.max_new_tokens,
            "min_new_tokens": self.min_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "do_sample": self.do_sample,
            "num_return_sequences": self.num_return_sequences,
        }
        if self.pad_token_id is not None:
            d["pad_token_id"] = self.pad_token_id
        if self.eos_token_id is not None:
            d["eos_token_id"] = self.eos_token_id
        d.update(self.extra_kwargs)
        return d


@dataclass
class DiffusionConfig:
    """
    Configuration parameters for diffusion image generation.
    """
    prompt: Union[str, List[str]] = ""
    negative_prompt: Optional[Union[str, List[str]]] = None
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    height: Optional[int] = None
    width: Optional[int] = None
    num_images_per_prompt: int = 1
    seed: Optional[int] = None
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "num_images_per_prompt": self.num_images_per_prompt,
        }
        if self.height is not None:
            d["height"] = self.height
        if self.width is not None:
            d["width"] = self.width
        if self.seed is not None:
            d["seed"] = self.seed
        d.update(self.extra_kwargs)
        return d


@dataclass
class ModelConfig:
    """
    General model configuration dataclass.
    """
    name_or_path: str = ""
    architecture: ModelArchitectureType = ModelArchitectureType.CAUSAL_LM
    precision: PrecisionType = PrecisionType.AUTO
    device_map: Optional[Union[str, Dict[str, Any]]] = None
    quantization: QuantizationType = QuantizationType.NONE
    gradient_checkpointing: bool = True
    use_cache: bool = True
    trust_remote_code: bool = True
    attn_backend: AttentionBackend = AttentionBackend.AUTO
    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: Optional[List[str]] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelOutput:
    """
    Container for model inference outputs.
    """
    text: Optional[Union[str, List[str]]] = None
    tokens: Optional[torch.Tensor] = None
    logits: Optional[torch.Tensor] = None
    embeddings: Optional[torch.Tensor] = None
    loss: Optional[torch.Tensor] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class DiffusionOutput:
    """
    Container for diffusion image generation outputs.
    """
    images: List[Any] = field(default_factory=list)
    seed: Optional[int] = None
    latents: Optional[torch.Tensor] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def image(self) -> Optional[Any]:
        """First generated image."""
        return self.images[0] if self.images else None

    def __getitem__(self, item: str) -> Any:
        if item == "image":
            return self.image
        return getattr(self, item)


@dataclass
class ModelInfo:
    """
    Metadata information for registered model components.
    """
    name: str
    cls_name: str
    module: str
    description: str
    aliases: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


__all__ = [
    "ModelArchitectureType",
    "PrecisionType",
    "DeviceMapType",
    "AttentionBackend",
    "SchedulerType",
    "QuantizationType",
    "GenerationConfig",
    "DiffusionConfig",
    "ModelConfig",
    "ModelOutput",
    "DiffusionOutput",
    "ModelInfo",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
