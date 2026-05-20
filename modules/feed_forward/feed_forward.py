"""
Feed-Forward Network implementations for TruthGPT
Provides various feed-forward architectures with different activation functions
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
from typing import Optional, Union, Callable, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class FeedForwardBase(ABC, nn.Module):
    """Abstract base class for feed-forward networks."""
    
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        """
        Initialize feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model
        self.d_ff = d_ff
        self.dropout = nn.Dropout(dropout)
    
    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the feed-forward network.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            
        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        pass

class FeedForward(FeedForwardBase):
    """
    Standard feed-forward network.
    
    This implements the standard feed-forward layer from the Transformer paper:
    FFN(x) = max(0, xW1 + b1)W2 + b2
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        activation: str = "relu",
        bias: bool = True
    ):
        """
        Initialize standard feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            activation: Activation function
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        
        # Linear layers
        self.linear1 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear2 = nn.Linear(d_ff, d_model, bias=bias)
        
        # Activation function
        if activation == "relu":
            self.activation = nn.ReLU()
        elif activation == "gelu":
            self.activation = nn.GELU()
        elif activation == "swish":
            self.activation = nn.SiLU()
        else:
            raise ValueError(f"Unsupported activation: {activation}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the feed-forward network."""
        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)
        return x

class GatedFeedForward(FeedForwardBase):
    """
    Gated feed-forward network.
    
    This implements a gated feed-forward layer where the activation function
    is applied to a gated version of the input.
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        activation: str = "gelu",
        bias: bool = True
    ):
        """
        Initialize gated feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            activation: Activation function
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        
        # Linear layers for gating
        self.linear1 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear2 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear3 = nn.Linear(d_ff, d_model, bias=bias)
        
        # Activation function
        if activation == "gelu":
            self.activation = nn.GELU()
        elif activation == "swish":
            self.activation = nn.SiLU()
        else:
            raise ValueError(f"Unsupported activation: {activation}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the gated feed-forward network."""
        # Apply gating
        gate = self.linear1(x)
        gate = self.activation(gate)
        
        # Apply second linear transformation
        x = self.linear2(x)
        
        # Combine gated and non-gated parts
        x = gate * x
        x = self.dropout(x)
        x = self.linear3(x)
        
        return x

class SwiGLU(FeedForwardBase):
    """
    SwiGLU feed-forward network.
    
    This implements the SwiGLU activation function as described in "GLU Variants Improve Transformer":
    SwiGLU(x) = Swish(xW1 + b1) * (xW2 + b2)
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        bias: bool = True
    ):
        """
        Initialize SwiGLU feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        
        # Linear layers for SwiGLU
        self.linear1 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear2 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear3 = nn.Linear(d_ff, d_model, bias=bias)
        
        # Swish activation
        self.swish = nn.SiLU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the SwiGLU feed-forward network."""
        # Apply SwiGLU
        gate = self.linear1(x)
        gate = self.swish(gate)
        
        x = self.linear2(x)
        x = gate * x
        x = self.dropout(x)
        x = self.linear3(x)
        
        return x

class ReGLU(FeedForwardBase):
    """
    ReGLU feed-forward network.
    
    This implements the ReGLU activation function:
    ReGLU(x) = ReLU(xW1 + b1) * (xW2 + b2)
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        bias: bool = True
    ):
        """
        Initialize ReGLU feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        
        # Linear layers for ReGLU
        self.linear1 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear2 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear3 = nn.Linear(d_ff, d_model, bias=bias)
        
        # ReLU activation
        self.relu = nn.ReLU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the ReGLU feed-forward network."""
        # Apply ReGLU
        gate = self.linear1(x)
        gate = self.relu(gate)
        
        x = self.linear2(x)
        x = gate * x
        x = self.dropout(x)
        x = self.linear3(x)
        
        return x

class GeGLU(FeedForwardBase):
    """
    GeGLU feed-forward network.
    
    This implements the GeGLU activation function:
    GeGLU(x) = GELU(xW1 + b1) * (xW2 + b2)
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        bias: bool = True
    ):
        """
        Initialize GeGLU feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        
        # Linear layers for GeGLU
        self.linear1 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear2 = nn.Linear(d_model, d_ff, bias=bias)
        self.linear3 = nn.Linear(d_ff, d_model, bias=bias)
        
        # GELU activation
        self.gelu = nn.GELU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the GeGLU feed-forward network."""
        # Apply GeGLU
        gate = self.linear1(x)
        gate = self.gelu(gate)
        
        x = self.linear2(x)
        x = gate * x
        x = self.dropout(x)
        x = self.linear3(x)
        
        return x

class AdaptiveFeedForward(FeedForwardBase):
    """
    Adaptive feed-forward network that can switch between different architectures.
    """
    
    def __init__(
        self, 
        d_model: int, 
        d_ff: int, 
        dropout: float = 0.1,
        architecture: str = "standard",
        bias: bool = True
    ):
        """
        Initialize adaptive feed-forward network.
        
        Args:
            d_model: Model dimension
            d_ff: Feed-forward dimension
            dropout: Dropout rate
            architecture: Architecture type
            bias: Whether to use bias in linear layers
        """
        super().__init__(d_model, d_ff, dropout)
        self.architecture = architecture
        
        if architecture == "standard":
            self.network = FeedForward(d_model, d_ff, dropout, bias=bias)
        elif architecture == "gated":
            self.network = GatedFeedForward(d_model, d_ff, dropout, bias=bias)
        elif architecture == "swiglu":
            self.network = SwiGLU(d_model, d_ff, dropout, bias=bias)
        elif architecture == "reglu":
            self.network = ReGLU(d_model, d_ff, dropout, bias=bias)
        elif architecture == "geglu":
            self.network = GeGLU(d_model, d_ff, dropout, bias=bias)
        else:
            raise ValueError(f"Unsupported architecture: {architecture}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the adaptive feed-forward network."""
        return self.network(x)
    
    def switch_architecture(self, new_architecture: str) -> None:
        """Switch to a different architecture."""
        if new_architecture == self.architecture:
            return
        
        self.architecture = new_architecture
        if new_architecture == "standard":
            self.network = FeedForward(self.d_model, self.d_ff, self.dropout.p)
        elif new_architecture == "gated":
            self.network = GatedFeedForward(self.d_model, self.d_ff, self.dropout.p)
        elif new_architecture == "swiglu":
            self.network = SwiGLU(self.d_model, self.d_ff, self.dropout.p)
        elif new_architecture == "reglu":
            self.network = ReGLU(self.d_model, self.d_ff, self.dropout.p)
        elif new_architecture == "geglu":
            self.network = GeGLU(self.d_model, self.d_ff, self.dropout.p)
        else:
            raise ValueError(f"Unsupported architecture: {new_architecture}")

# Factory functions
def create_feed_forward(
    d_model: int,
    d_ff: int,
    dropout: float = 0.1,
    architecture: str = "standard",
    bias: bool = True,
    **kwargs
) -> FeedForwardBase:
    """
    Create a feed-forward network instance.
    
    Args:
        d_model: Model dimension
        d_ff: Feed-forward dimension
        dropout: Dropout rate
        architecture: Architecture type
        bias: Whether to use bias in linear layers
        **kwargs: Additional arguments
        
    Returns:
        Feed-forward network instance
    """
    if architecture == "standard":
        return FeedForward(d_model, d_ff, dropout, bias=bias, **kwargs)
    elif architecture == "gated":
        return GatedFeedForward(d_model, d_ff, dropout, bias=bias, **kwargs)
    elif architecture == "swiglu":
        return SwiGLU(d_model, d_ff, dropout, bias=bias)
    elif architecture == "reglu":
        return ReGLU(d_model, d_ff, dropout, bias=bias)
    elif architecture == "geglu":
        return GeGLU(d_model, d_ff, dropout, bias=bias)
    elif architecture == "adaptive":
        return AdaptiveFeedForward(d_model, d_ff, dropout, bias=bias, **kwargs)
    else:
        raise ValueError(f"Unsupported architecture: {architecture}")

def create_swiglu(
    d_model: int,
    d_ff: int,
    dropout: float = 0.1,
    bias: bool = True
) -> SwiGLU:
    """Create a SwiGLU feed-forward network."""
    return SwiGLU(d_model, d_ff, dropout, bias)

def create_gated_ffn(
    d_model: int,
    d_ff: int,
    dropout: float = 0.1,
    bias: bool = True
) -> GatedFeedForward:
    """Create a gated feed-forward network."""
    return GatedFeedForward(d_model, d_ff, dropout, bias)




