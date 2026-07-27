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

@dataclass
class GenerationConfig:
    max_new_tokens: int = 64
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True
    num_beams: int = 1
