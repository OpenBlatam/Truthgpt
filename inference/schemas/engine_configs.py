from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator

class TensorRTBackend(str, Enum):
    TENSORRT_ONLY = "tensorrt_only"
    TENSORRT_RUST = "tensorrt_rust"
    TENSORRT_CPP = "tensorrt_cpp"
    AUTO = "auto"

class VLLMBackend(str, Enum):
    VLLM_ONLY = "vllm_only"
    VLLM_RUST = "vllm_rust"
    VLLM_CPP = "vllm_cpp"
    AUTO = "auto"

class GenerationConfig(BaseModel):
    max_new_tokens: int = Field(default=128, ge=1, le=8192, description="Maximum number of tokens to generate.")
    temperature: float = Field(default=0.8, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Nucleus sampling probability.")
    top_k: int = Field(default=50, ge=0, description="Top-k sampling.")
    repetition_penalty: float = Field(default=1.1, ge=1.0, description="Repetition penalty factor.")
    do_sample: bool = Field(default=True, description="Whether to use sampling or greedy decoding.")
    num_beams: int = Field(default=1, ge=1, description="Number of beams for beam search.")

class TensorRTConfig(BaseModel):
    max_batch_size: int = Field(default=8, ge=1, description="Maximum batch size.")
    max_seq_length: int = Field(default=2048, ge=1, description="Maximum sequence length.")
    use_rust_kv_cache: bool = Field(default=True, description="Enable Polyglot Rust KV Cache.")
    use_cpp_attention: bool = Field(default=True, description="Enable Polyglot C++ Attention kernels.")
    backend_mode: TensorRTBackend = Field(default=TensorRTBackend.AUTO, description="Execution backend mode.")
    precision: str = Field(default="float16", description="Weights precision.")
    use_quantization: bool = Field(default=False, description="Enable INT8/FP8 quantization.")

class VLLMConfig(BaseModel):
    tensor_parallel_size: int = Field(default=1, ge=1, description="Number of GPUs for tensor parallelism.")
    gpu_memory_utilization: float = Field(default=0.9, ge=0.1, le=1.0, description="GPU memory utilization ratio.")
    max_model_len: Optional[int] = Field(default=None, description="Maximum model context length.")
    dtype: str = Field(default="auto", description="Data type for model weights.")
    quantization: Optional[str] = Field(default=None, description="Quantization method (awq, gptq, etc.).")
    trust_remote_code: bool = Field(default=False, description="Trust remote code execution from HF Hub.")
    enable_prefix_caching: bool = Field(default=True, description="Enable vLLM automatic prefix caching.")
    use_rust_kv_cache: bool = Field(default=True, description="Enable Polyglot Rust KV Cache.")
    backend_mode: VLLMBackend = Field(default=VLLMBackend.AUTO, description="Execution backend mode.")
