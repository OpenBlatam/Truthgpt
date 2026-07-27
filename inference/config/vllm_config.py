"""
vLLM Engine Configuration
=========================

Configuration classes for vLLM engine initialization.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class BackendMode(Enum):
    VLLM_ONLY = "vllm_only"
    VLLM_RUST = "vllm_rust"
    VLLM_CPP = "vllm_cpp"
    AUTO = "auto"

@dataclass
class VLLMConfig:
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    max_model_len: Optional[int] = None
    dtype: str = "auto"
    quantization: Optional[str] = None
    trust_remote_code: bool = False
    enable_prefix_caching: bool = True
    use_rust_kv_cache: bool = True
    backend_mode: BackendMode = BackendMode.AUTO
