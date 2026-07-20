from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
import numpy as np
import time
from .backend import Backend, get_best_backend, is_backend_available

from .constants import *
from .config import *


# ═══════════════════════════════════════════════════════════════════════════════
# TOKEN SAMPLING
# ═══════════════════════════════════════════════════════════════════════════════

class TokenSampler:
    """
    Token sampling with various strategies.
    
    Supports:
    - Greedy decoding (argmax)
    - Temperature scaling
    - Top-K filtering
    - Top-P (nucleus) filtering
    - Repetition penalty
    
    Example:
        >>> sampler = TokenSampler(seed=42)
        >>> token = sampler.sample(logits, config, prev_tokens=[1, 2, 3])
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize TokenSampler.
        
        Args:
            seed: Random seed for reproducibility
        """
        self._rng = np.random.default_rng(seed)
    
    def sample(
        self,
        logits: np.ndarray,
        config: GenerationConfig,
        prev_tokens: Optional[List[int]] = None
    ) -> int:
        """
        Sample next token from logits.
        
        Args:
            logits: Logits array [vocab_size]
            config: Generation configuration
            prev_tokens: Previous tokens for repetition penalty
            
        Returns:
            Sampled token ID
            
        Algorithm:
            1. Apply repetition penalty to logits
            2. If greedy: return argmax
            3. Apply temperature scaling
            4. Convert to probabilities (softmax)
            5. Apply top-k filtering
            6. Apply top-p (nucleus) filtering
            7. Sample from filtered distribution
        """
        if len(logits) == 0:
            raise ValueError("logits array cannot be empty")
        
        # Work with float64 for numerical stability
        logits = logits.astype(np.float64).copy()
        
        # Apply repetition penalty to discourage repetition
        if config.repetition_penalty != 1.0 and prev_tokens:
            logits = self._apply_repetition_penalty(logits, prev_tokens, config.repetition_penalty)
        
        # Greedy decoding: return token with highest probability
        if not config.do_sample:
            return int(np.argmax(logits))
        
        # Temperature scaling: higher temperature = more random
        if config.temperature != 1.0:
            logits = logits / config.temperature
        
        # Convert to probabilities using numerically stable softmax
        probs = self._softmax(logits)
        
        # Apply top-k filtering: keep only top-k tokens
        if config.top_k > 0 and config.top_k < len(probs):
            probs = self._apply_top_k(probs, config.top_k)
        
        # Apply top-p (nucleus) filtering: keep tokens until cumulative prob >= top_p
        if config.top_p < 1.0:
            probs = self._apply_top_p(probs, config.top_p)
        
        # Sample from filtered distribution
        return int(self._rng.choice(len(probs), p=probs))
    
    def _apply_repetition_penalty(
        self,
        logits: np.ndarray,
        prev_tokens: List[int],
        penalty: float
    ) -> np.ndarray:
        """
        Apply repetition penalty to logits.
        
        Args:
            logits: Logits array
            prev_tokens: Previously generated tokens
            penalty: Penalty factor (>1.0 reduces probability of repeated tokens)
            
        Returns:
            Modified logits array
        """
        # Get unique previous tokens to avoid double-penalizing
        unique_prev_tokens = set(prev_tokens)
        
        for token_id in unique_prev_tokens:
            if 0 <= token_id < len(logits):
                # Reduce probability of repeating this token
                if logits[token_id] > 0:
                    logits[token_id] /= penalty
                else:
                    logits[token_id] *= penalty
        
        return logits
    
    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """
        Compute numerically stable softmax.
        
        Args:
            logits: Logits array
            
        Returns:
            Probability distribution
        """
        # Subtract max for numerical stability
        logits_shifted = logits - logits.max()
        exp_logits = np.exp(logits_shifted)
        return exp_logits / (exp_logits.sum() + EPSILON)
    
    def _apply_top_k(self, probs: np.ndarray, k: int) -> np.ndarray:
        """
        Apply top-k filtering to probabilities.
        
        Args:
            probs: Probability distribution
            k: Number of top tokens to keep
            
        Returns:
            Filtered probability distribution
        """
        # Get indices of top-k tokens
        top_k_indices = np.argsort(probs)[-k:]
        
        # Create mask for top-k tokens
        mask = np.zeros_like(probs)
        mask[top_k_indices] = 1.0
        
        # Zero out non-top-k probabilities and renormalize
        filtered_probs = probs * mask
        return filtered_probs / (filtered_probs.sum() + EPSILON)
    
    def _apply_top_p(self, probs: np.ndarray, p: float) -> np.ndarray:
        """
        Apply top-p (nucleus) filtering to probabilities.
        
        Args:
            probs: Probability distribution
            p: Cumulative probability threshold
            
        Returns:
            Filtered probability distribution
        """
        # Sort probabilities in descending order
        sorted_indices = np.argsort(probs)[::-1]
        sorted_probs = probs[sorted_indices]
        
        # Compute cumulative probabilities
        cumsum = np.cumsum(sorted_probs)
        
        # Find cutoff index where cumulative prob >= p
        cutoff_idx = np.searchsorted(cumsum, p) + 1
        cutoff_idx = min(cutoff_idx, len(probs))
        
        # Create mask for tokens up to cutoff
        mask = np.zeros_like(probs)
        mask[sorted_indices[:cutoff_idx]] = 1.0
        
        # Zero out tokens beyond cutoff and renormalize
        filtered_probs = probs * mask
        return filtered_probs / (filtered_probs.sum() + EPSILON)


# ═══════════════════════════════════════════════════════════════════════════════
# INFERENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class InferenceEngine:
    """
    Unified Inference Engine with automatic backend selection.
    
    Supports text generation with:
    - Greedy decoding (deterministic, fastest)
    - Sampling (temperature, top-k, top-p)
    - Beam search (multi-candidate generation)
    - Repetition penalty
    
    Example:
        >>> engine = InferenceEngine(seed=42)
        >>> config = GenerationConfig.sampling(temperature=0.7)
        >>> result = engine.generate(prompt_ids, model.forward, config)
        >>> print(f"{result.tokens_per_second:.0f} tokens/sec")
    """
    
    def __init__(
        self,
        config: Optional[InferenceConfig] = None,
        seed: int = 42,
        backend: Optional[Backend] = None
    ):
        """
        Initialize Inference Engine.
        
        Args:
            config: Inference configuration
            seed: Random seed for reproducibility
            backend: Force specific backend (None = auto-select)
        """
        if config is None:
            config = InferenceConfig(seed=seed)
        
        self.config = config
        self._backend = backend or get_best_backend('inference')
        self._sampler = TokenSampler(seed=config.seed)
        self._impl = self._create_implementation()
    
    def _create_implementation(self):
        """
        Create backend-specific implementation.
        
        Returns:
            Backend implementation or None (use Python fallback)
        """
        if self._backend == Backend.CPP and is_backend_available(Backend.CPP):
            return self._create_cpp_impl()
        # Add other backend implementations here
        return None
    
    def _create_cpp_impl(self):
        """
        Create C++ implementation.
        
        Returns:
            C++ inference engine or None if unavailable
        """
        # TODO: Implement C++ inference engine
        # Would use C++ bindings for faster inference
        return None
    
    def generate(
        self,
        input_ids: List[int],
        forward_fn: Callable[[List[int]], np.ndarray],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate tokens given input IDs.
        
        Args:
            input_ids: Input token IDs
            forward_fn: Model forward function (tokens -> logits)
            config: Generation configuration
            **kwargs: Config overrides (merged into config)
            
        Returns:
            GenerationResult with generated tokens and statistics
            
        Raises:
            ValueError: If input_ids is empty or forward_fn is invalid
        """
        if not input_ids:
            raise ValueError("input_ids cannot be empty")
        
        # Merge kwargs into config
        if config is None:
            config = GenerationConfig(**kwargs)
        else:
            # Update config with kwargs
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        start_time = time.perf_counter()
        
        # Initialize token sequence with input
        tokens = list(input_ids)
        generated_count = 0
        finish_reason = FINISH_REASON_MAX_LENGTH
        
        # Generate tokens one by one
        for _ in range(config.max_new_tokens):
            # Get logits from model forward pass
            logits = forward_fn(tokens)
            
            # Ensure logits is a flat numpy array
            if isinstance(logits, np.ndarray):
                logits = logits.flatten()
            else:
                logits = np.array(logits).flatten()
            
            # Sample next token
            if config.num_beams > 1:
                # TODO: Implement proper beam search
                # For now, use regular sampling
                next_token = self._sampler.sample(logits, config, tokens)
            else:
                next_token = self._sampler.sample(logits, config, tokens)
            
            # Append token to sequence
            tokens.append(int(next_token))
            generated_count += 1
            
            # Check for end-of-sequence token
            if config.eos_token_id is not None and next_token == config.eos_token_id:
                finish_reason = FINISH_REASON_EOS
                break
            
            # Check timeout
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if elapsed_ms > self.config.timeout_ms:
                finish_reason = FINISH_REASON_TIMEOUT
                break
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return GenerationResult(
            token_ids=tokens,
            tokens_generated=generated_count,
            generation_time_ms=elapsed_ms,
            finish_reason=finish_reason
        )
    
    def generate_batch(
        self,
        batch_input_ids: List[List[int]],
        forward_fn: Callable[[List[List[int]]], np.ndarray],
        config: Optional[GenerationConfig] = None
    ) -> List[GenerationResult]:
        """
        Generate tokens for a batch of inputs.
        
        Args:
            batch_input_ids: List of input token ID lists
            forward_fn: Batched forward function (batch -> logits)
            config: Generation configuration
            
        Returns:
            List of GenerationResult for each input
            
        Note:
            Currently processes sequentially. TODO: Implement proper batched generation
            with padding and attention masks.
        """
        if not batch_input_ids:
            return []
        
        if len(batch_input_ids) > self.config.max_batch_size:
            raise ValueError(
                f"Batch size {len(batch_input_ids)} exceeds max_batch_size "
                f"{self.config.max_batch_size}"
            )
        
        results = []
        for input_ids in batch_input_ids:
            # Create single-input forward function
            single_forward = lambda t: forward_fn([t])[0]
            result = self.generate(input_ids, single_forward, config)
            results.append(result)
        
        return results
    
    @property
    def backend(self) -> Backend:
        """Get current backend."""
        return self._backend
    
    def __repr__(self) -> str:
        return (f"InferenceEngine(seed={self.config.seed}, "
                f"backend={self._backend.name}, "
                f"use_cache={self.config.use_cache})")

