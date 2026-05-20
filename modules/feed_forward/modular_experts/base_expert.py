"""
Base Expert Module
Abstract base class and interfaces for all expert implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import logging
import math

class ExpertType(Enum):
    """Expert type classifications."""
    REASONING = "reasoning"
    COMPUTATION = "computation"
    MATHEMATICAL = "mathematical"
    LOGICAL = "logical"
    LANGUAGE = "language"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    SPECIALIZED = "specialized"

class ExpertStatus(Enum):
    """Expert status states."""
    IDLE = "idle"
    PROCESSING = "processing"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class ExpertResult:
    """Result of expert processing."""
    output: torch.Tensor
    processing_time: float
    expert_id: str
    expert_type: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class ExpertConfig:
    """Base expert configuration."""
    expert_id: str
    expert_type: ExpertType
    hidden_size: int = 512
    intermediate_size: int = 2048
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1
    activation: str = "gelu"
    use_bias: bool = True
    layer_norm_eps: float = 1e-5
    max_sequence_length: int = 2048
    enable_gradient_checkpointing: bool = False
    enable_quantization: bool = False
    quantization_bits: int = 8
    enable_pruning: bool = False
    pruning_ratio: float = 0.1
    enable_caching: bool = True
    cache_size: int = 100
    enable_metrics: bool = True
    enable_logging: bool = True

class BaseExpert(ABC):
    """
    Abstract base class for all expert implementations.
    """
    
    def __init__(self, config: ExpertConfig):
        self.config = config
        self.logger = logging.getLogger(f'{self.__class__.__name__}_{config.expert_id}')
        self.status = ExpertStatus.IDLE
        self.metrics = {}
        self.cache = {} if config.enable_caching else None
        self.model = None
        self._initialized = False
        self._processing_count = 0
        self._total_processing_time = 0.0
        
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the expert."""
        pass
    
    @abstractmethod
    def process_tokens(
        self, 
        input_tokens: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertResult:
        """
        Process tokens through the expert.
        
        Args:
            input_tokens: Input token tensor [batch, seq_len, hidden_size]
            attention_mask: Optional attention mask [batch, seq_len]
            context: Optional processing context
            
        Returns:
            ExpertResult with processed output
        """
        pass
    
    @abstractmethod
    def get_expert_info(self) -> Dict[str, Any]:
        """Get expert information and statistics."""
        pass
    
    def validate_input(self, input_tokens: torch.Tensor) -> None:
        """Validate input tensor."""
        if not isinstance(input_tokens, torch.Tensor):
            raise ValueError("Input must be a torch.Tensor")
        
        if input_tokens.dim() != 3:
            raise ValueError("Input must be 3D tensor [batch, seq_len, hidden_size]")
        
        if input_tokens.size(-1) != self.config.hidden_size:
            raise ValueError(f"Hidden size mismatch: expected {self.config.hidden_size}, got {input_tokens.size(-1)}")
        
        if input_tokens.size(1) > self.config.max_sequence_length:
            raise ValueError(f"Sequence length {input_tokens.size(1)} exceeds maximum {self.config.max_sequence_length}")
    
    def get_cache_key(self, input_tokens: torch.Tensor, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for input."""
        if not self.cache:
            return None
        
        # Create hash from tensor and context
        tensor_hash = hash(input_tokens.data.tobytes())
        context_hash = hash(str(context)) if context else 0
        return f"{tensor_hash}_{context_hash}"
    
    def get_cached_result(self, cache_key: str) -> Optional[ExpertResult]:
        """Get cached processing result."""
        if not self.cache or cache_key not in self.cache:
            return None
        
        cached_result, timestamp = self.cache[cache_key]
        
        # Check cache expiry (10 minutes)
        if time.time() - timestamp > 600:
            del self.cache[cache_key]
            return None
        
        return cached_result
    
    def cache_result(self, cache_key: str, result: ExpertResult) -> None:
        """Cache processing result."""
        if not self.cache:
            return
        
        # Implement LRU cache
        if len(self.cache) >= self.config.cache_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = (result, time.time())
    
    def record_metrics(self, result: ExpertResult) -> None:
        """Record expert metrics."""
        if not self.config.enable_metrics:
            return
        
        self.metrics.setdefault('processing_time', []).append(result.processing_time)
        self.metrics.setdefault('confidence', []).append(result.confidence)
        self.metrics.setdefault('success_rate', []).append(1.0 if result.success else 0.0)
        
        # Update processing statistics
        self._processing_count += 1
        self._total_processing_time += result.processing_time
        
        # Keep only recent metrics
        max_metrics = 1000
        for key in self.metrics:
            if len(self.metrics[key]) > max_metrics:
                self.metrics[key] = self.metrics[key][-max_metrics:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get expert metrics."""
        metrics = {
            'status': self.status.value,
            'processing_count': self._processing_count,
            'total_processing_time': self._total_processing_time,
            'average_processing_time': self._total_processing_time / max(self._processing_count, 1),
            'cache_size': len(self.cache) if self.cache else 0
        }
        
        if self.metrics:
            for key, values in self.metrics.items():
                if values:
                    metrics[f'{key}_mean'] = np.mean(values)
                    metrics[f'{key}_std'] = np.std(values)
                    metrics[f'{key}_min'] = np.min(values)
                    metrics[f'{key}_max'] = np.max(values)
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset expert metrics."""
        self.metrics.clear()
        self._processing_count = 0
        self._total_processing_time = 0.0
    
    def log_processing(self, result: ExpertResult, input_shape: Tuple[int, ...]) -> None:
        """Log processing information."""
        if not self.config.enable_logging:
            return
        
        self.logger.info(
            f"Expert processing completed: "
            f"expert_id={result.expert_id}, "
            f"expert_type={result.expert_type}, "
            f"confidence={result.confidence:.3f}, "
            f"time={result.processing_time:.4f}s, "
            f"success={result.success}, "
            f"input_shape={input_shape}"
        )
    
    def set_status(self, status: ExpertStatus) -> None:
        """Set expert status."""
        self.status = status
        self.logger.debug(f"Expert status changed to {status.value}")
    
    def is_available(self) -> bool:
        """Check if expert is available for processing."""
        return self.status in [ExpertStatus.IDLE, ExpertStatus.PROCESSING]
    
    def is_healthy(self) -> bool:
        """Check if expert is healthy."""
        return self.status != ExpertStatus.ERROR and self.status != ExpertStatus.DISABLED
    
    @property
    def is_initialized(self) -> bool:
        """Check if expert is initialized."""
        return self._initialized
    
    def shutdown(self) -> None:
        """Shutdown the expert."""
        self.set_status(ExpertStatus.DISABLED)
        self.cache.clear() if self.cache else None
        self.reset_metrics()
        self._initialized = False
        self.logger.info(f"Expert {self.config.expert_id} shutdown")

class ExpertLayer(nn.Module):
    """Base expert layer implementation."""
    
    def __init__(self, config: ExpertConfig):
        super().__init__()
        self.config = config
        
        # Input projection
        self.input_projection = nn.Linear(
            config.hidden_size, 
            config.hidden_size,
            bias=config.use_bias
        )
        
        # Hidden layers
        self.hidden_layers = nn.ModuleList([
            ExpertHiddenLayer(config, i) 
            for i in range(config.num_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(
            config.hidden_size,
            config.hidden_size,
            bias=config.use_bias
        )
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(
            config.hidden_size, 
            eps=config.layer_norm_eps
        )
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
        
        # Activation function
        self.activation = self._get_activation(config.activation)
    
    def _get_activation(self, activation_name: str) -> nn.Module:
        """Get activation function."""
        activations = {
            'relu': nn.ReLU(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'mish': nn.Mish(),
            'leaky_relu': nn.LeakyReLU(),
            'elu': nn.ELU()
        }
        return activations.get(activation_name, nn.GELU())
    
    def forward(
        self, 
        x: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through expert layer."""
        # Input projection
        x = self.input_projection(x)
        
        # Hidden layers
        for layer in self.hidden_layers:
            if self.config.enable_gradient_checkpointing:
                x = torch.utils.checkpoint.checkpoint(layer, x, attention_mask)
            else:
                x = layer(x, attention_mask)
        
        # Output projection
        x = self.output_projection(x)
        
        # Layer normalization and dropout
        x = self.layer_norm(x)
        x = self.dropout(x)
        
        return x

class ExpertHiddenLayer(nn.Module):
    """Hidden layer for expert."""
    
    def __init__(self, config: ExpertConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        # Self-attention
        self.self_attention = nn.MultiheadAttention(
            embed_dim=config.hidden_size,
            num_heads=config.num_heads,
            dropout=config.dropout,
            batch_first=True
        )
        
        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(config.hidden_size, config.intermediate_size, bias=config.use_bias),
            self._get_activation(config.activation),
            nn.Dropout(config.dropout),
            nn.Linear(config.intermediate_size, config.hidden_size, bias=config.use_bias)
        )
        
        # Layer normalization
        self.layer_norm1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.layer_norm2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
    
    def _get_activation(self, activation_name: str) -> nn.Module:
        """Get activation function."""
        activations = {
            'relu': nn.ReLU(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'mish': nn.Mish(),
            'leaky_relu': nn.LeakyReLU(),
            'elu': nn.ELU()
        }
        return activations.get(activation_name, nn.GELU())
    
    def forward(
        self, 
        x: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through hidden layer."""
        # Self-attention
        attn_output, _ = self.self_attention(
            x, x, x,
            key_padding_mask=attention_mask
        )
        x = x + self.dropout(attn_output)
        x = self.layer_norm1(x)
        
        # Feed-forward
        ff_output = self.feed_forward(x)
        x = x + self.dropout(ff_output)
        x = self.layer_norm2(x)
        
        return x




