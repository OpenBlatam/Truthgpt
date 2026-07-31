from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import torch

class Backend(Enum):
    PYTORCH = "pytorch"
    RUST = "rust"
    CPP = "cpp"
    AUTO = "auto"

@dataclass
class InferenceConfig:
    max_batch_size: int = 8
    max_seq_length: int = 512
    use_amp: bool = True
    amp_dtype: torch.dtype = torch.float16
    backend: Backend = Backend.AUTO
    use_kv_cache: bool = True
    use_rust_tokenizer: bool = True
    use_cpp_attention: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary representation with type normalization."""
        return {
            "max_batch_size": self.max_batch_size,
            "max_seq_length": self.max_seq_length,
            "use_amp": self.use_amp,
            "amp_dtype": str(self.amp_dtype),
            "backend": self.backend.value if isinstance(self.backend, Backend) else str(self.backend),
            "use_kv_cache": self.use_kv_cache,
            "use_rust_tokenizer": self.use_rust_tokenizer,
            "use_cpp_attention": self.use_cpp_attention,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferenceConfig":
        """Instantiate InferenceConfig from dictionary with validation."""
        kwargs = dict(data)
        if "backend" in kwargs and isinstance(kwargs["backend"], str):
            kwargs["backend"] = Backend(kwargs["backend"])
        if "amp_dtype" in kwargs and isinstance(kwargs["amp_dtype"], str):
            kwargs["amp_dtype"] = getattr(torch, kwargs["amp_dtype"].replace("torch.", ""), torch.float16)
        return cls(**kwargs)


@dataclass
class GenerationConfig:
    max_new_tokens: int = 64
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True
    num_beams: int = 1

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
        return cls(**filtered)

