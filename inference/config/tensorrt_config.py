"""
TensorRT-LLM Engine Configuration
=================================

Configuration classes for TensorRT-LLM engine initialization.
"""

from dataclasses import dataclass
from enum import Enum

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
