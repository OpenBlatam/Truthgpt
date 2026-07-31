"""
TensorRT-LLM Engine Configuration
=================================

Configuration classes for TensorRT-LLM engine initialization.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any

class TensorRTBackend(Enum):
    TENSORRT_ONLY = "tensorrt_only"
    TENSORRT_RUST = "tensorrt_rust"
    TENSORRT_CPP = "tensorrt_cpp"
    AUTO = "auto"

@dataclass
class TensorRTConfig:
    max_batch_size: int = 8
    max_seq_length: int = 2048
    use_rust_kv_cache: bool = True
    use_cpp_attention: bool = True
    backend_mode: TensorRTBackend = TensorRTBackend.AUTO
    precision: str = "float16"
    use_quantization: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert TensorRT configuration to a standard dictionary."""
        return {
            "max_batch_size": self.max_batch_size,
            "max_seq_length": self.max_seq_length,
            "use_rust_kv_cache": self.use_rust_kv_cache,
            "use_cpp_attention": self.use_cpp_attention,
            "backend_mode": self.backend_mode.value if isinstance(self.backend_mode, TensorRTBackend) else str(self.backend_mode),
            "precision": self.precision,
            "use_quantization": self.use_quantization,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TensorRTConfig":
        """Instantiate TensorRTConfig from a dictionary."""
        kwargs = dict(data)
        if "backend_mode" in kwargs and isinstance(kwargs["backend_mode"], str):
            kwargs["backend_mode"] = TensorRTBackend(kwargs["backend_mode"])
        return cls(**kwargs)

