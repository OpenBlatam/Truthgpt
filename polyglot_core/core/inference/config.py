from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
import numpy as np
import time
from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available

from .constants import *

class GenerationConfig:
    """
    Configuration for text generation.
    
    Attributes:
        max_new_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (higher = more random)
        top_k: Keep only top-k tokens for sampling
        top_p: Nucleus sampling threshold (cumulative probability)
        repetition_penalty: Penalty for repeating tokens (>1.0 = less repetition)
        do_sample: Whether to use sampling (False = greedy)
        num_beams: Number of beams for beam search
        eos_token_id: End-of-sequence token ID
        pad_token_id: Padding token ID
    """
    max_new_tokens: int = field(default=DEFAULT_MAX_NEW_TOKENS)
    temperature: float = field(default=DEFAULT_TEMPERATURE)
    top_k: int = field(default=DEFAULT_TOP_K)
    top_p: float = field(default=DEFAULT_TOP_P)
    repetition_penalty: float = field(default=DEFAULT_REPETITION_PENALTY)
    do_sample: bool = True
    num_beams: int = field(default=DEFAULT_NUM_BEAMS)
    eos_token_id: Optional[int] = None
    pad_token_id: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_new_tokens <= 0:
            raise ValueError(f"max_new_tokens must be positive, got {self.max_new_tokens}")
        if self.temperature <= 0:
            raise ValueError(f"temperature must be positive, got {self.temperature}")
        if self.top_k < 0:
            raise ValueError(f"top_k must be non-negative, got {self.top_k}")
        if not 0 < self.top_p <= 1.0:
            raise ValueError(f"top_p must be in (0, 1], got {self.top_p}")
        if self.repetition_penalty <= 0:
            raise ValueError(f"repetition_penalty must be positive, got {self.repetition_penalty}")
        if self.num_beams < 1:
            raise ValueError(f"num_beams must be >= 1, got {self.num_beams}")
    
    @classmethod
    def greedy(cls) -> "GenerationConfig":
        """
        Greedy decoding - deterministic, fastest.
        
        Always selects the token with highest probability.
        """
        return cls(do_sample=False, temperature=1.0, num_beams=1)
    
    @classmethod
    def sampling(cls, temperature: float = 0.7, top_p: float = 0.9) -> "GenerationConfig":
        """
        Sampling with temperature and nucleus.
        
        Args:
            temperature: Sampling temperature (default: 0.7)
            top_p: Nucleus sampling threshold (default: 0.9)
        """
        return cls(do_sample=True, temperature=temperature, top_p=top_p)
    
    @classmethod
    def beam_search(cls, num_beams: int = 4) -> "GenerationConfig":
        """
        Beam search for best sequence.
        
        Args:
            num_beams: Number of beams to keep (default: 4)
        """
        return cls(do_sample=False, num_beams=num_beams)
    
    @classmethod
    def creative(cls) -> "GenerationConfig":
        """
        Creative/diverse generation configuration.
        
        High temperature and top-p for more diverse outputs.
        """
        return cls(
            do_sample=True,
            temperature=0.9,
            top_k=100,
            top_p=0.95,
            repetition_penalty=1.1
        )
    
    @classmethod
    def factual(cls) -> "GenerationConfig":
        """
        Factual/deterministic generation configuration.
        
        Low temperature and conservative sampling for factual outputs.
        """
        return cls(
            do_sample=True,
            temperature=0.3,
            top_k=20,
            top_p=0.85,
            repetition_penalty=1.05
        )

class InferenceConfig:
    """
    Configuration for inference engine.
    
    Attributes:
        seed: Random seed for reproducibility
        use_cache: Whether to use KV cache
        max_batch_size: Maximum batch size for batched generation
        timeout_ms: Timeout in milliseconds
    """
    seed: int = 42
    use_cache: bool = True
    max_batch_size: int = 8
    timeout_ms: float = 30000.0
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_batch_size <= 0:
            raise ValueError(f"max_batch_size must be positive, got {self.max_batch_size}")
        if self.timeout_ms <= 0:
            raise ValueError(f"timeout_ms must be positive, got {self.timeout_ms}")

class GenerationResult:
    """
    Result from text generation.
    
    Attributes:
        token_ids: Generated token IDs (including input)
        tokens_generated: Number of newly generated tokens
        generation_time_ms: Generation time in milliseconds
        finish_reason: Reason for stopping (max_length, eos, timeout)
    """
    token_ids: List[int]
    tokens_generated: int
    generation_time_ms: float
    finish_reason: str = field(default=FINISH_REASON_MAX_LENGTH)
    
    @property
    def tokens_per_second(self) -> float:
        """
        Calculate tokens per second generation rate.
        
        Returns:
            Tokens per second (0.0 if generation_time_ms <= 0)
        """
        if self.generation_time_ms <= 0:
            return 0.0
        return self.tokens_generated / (self.generation_time_ms / 1000.0)

