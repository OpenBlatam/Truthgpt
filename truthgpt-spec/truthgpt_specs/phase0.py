"""
TruthGPT Phase 0 Specification Reference Implementation.

Implements core transformer optimizations, attention mechanisms, feed-forward networks,
and optimizer abstractions defined in specs/phase0/core.md.
"""

from dataclasses import dataclass
from typing import Optional, Any
import torch
import torch.nn as nn


@dataclass
class Phase0Config:
    """Configuration for TruthGPT Phase 0 Foundation."""
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 2048
    vocab_size: int = 50000
    max_sequence_length: int = 4096
    use_gradient_checkpointing: bool = False
    use_mixed_precision: bool = False
    use_flash_attention: bool = False
    use_dynamic_batching: bool = False

    def __post_init__(self):
        if self.d_model <= 0:
            raise ValueError(f"d_model must be positive, got {self.d_model}")
        if self.n_heads <= 0:
            raise ValueError(f"n_heads must be positive, got {self.n_heads}")
        if self.n_layers <= 0:
            raise ValueError(f"n_layers must be positive, got {self.n_layers}")
        if self.d_ff <= 0:
            raise ValueError(f"d_ff must be positive, got {self.d_ff}")
        if self.vocab_size <= 0:
            raise ValueError(f"vocab_size must be positive, got {self.vocab_size}")
        if self.max_sequence_length <= 0:
            raise ValueError(f"max_sequence_length must be positive, got {self.max_sequence_length}")

    def is_valid(self) -> bool:
        """Validates configuration parameters."""
        return (
            self.d_model > 0 and
            self.n_heads > 0 and
            self.n_layers > 0 and
            self.d_ff > 0 and
            self.vocab_size > 0 and
            self.max_sequence_length > 0
        )


class AttentionMechanism(nn.Module):
    """Reference multi-head attention mechanism for Phase 0."""

    def __init__(self, config: Phase0Config):
        super().__init__()
        self.config = config
        self.mha = nn.MultiheadAttention(
            embed_dim=config.d_model,
            num_heads=config.n_heads,
            batch_first=True
        )
        self.norm = nn.LayerNorm(config.d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.mha(x, x, x)
        return self.norm(x + out)


class FeedForwardNetwork(nn.Module):
    """Reference feed-forward network for Phase 0."""

    def __init__(self, config: Phase0Config):
        super().__init__()
        self.config = config
        self.linear1 = nn.Linear(config.d_model, config.d_ff)
        self.activation = nn.GELU()
        self.linear2 = nn.Linear(config.d_ff, config.d_model)
        self.norm = nn.LayerNorm(config.d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        hidden = self.activation(self.linear1(x))
        out = self.linear2(hidden)
        return self.norm(residual + out)


class OptimizedModelWrapper(nn.Module):
    """Execution wrapper for Phase 0 optimized models."""

    def __init__(self, model: nn.Module, config: Phase0Config):
        super().__init__()
        self._wrapped_model = model
        self.config = config

    def forward(self, *args, **kwargs):
        if self.config.use_mixed_precision and torch.cuda.is_available():
            with torch.amp.autocast(device_type="cuda"):
                return self._wrapped_model(*args, **kwargs)
        return self._wrapped_model(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self._wrapped_model, name)


class TransformerOptimizer:
    """Core optimizer orchestrating Phase 0 transformations and migrations."""

    def __init__(self, config: Phase0Config):
        self.config = config

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """Applies Phase 0 optimizations to model."""
        model.eval()
        if self.config.use_gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()
        # Warm up to eliminate cold-start threadpool initialization on CPU
        try:
            dummy = torch.zeros(1, 2, self.config.d_model)
            with torch.no_grad():
                model(dummy, dummy)
        except Exception:
            pass
        return OptimizedModelWrapper(model, self.config)

    def migrate_to_altair(self) -> Any:
        """State transition to Altair Hyper-Speed."""
        from .altair import AltairOptimizer, AltairConfig
        altair_config = AltairConfig(
            enable_lightning_mode=True,
            enable_zero_copy=True
        )
        return AltairOptimizer(altair_config)

    def migrate_to_bellatrix(self) -> Any:
        """State transition to Bellatrix Ultra-Optimization."""
        from .bellatrix import BellatrixOptimizer, BellatrixConfig
        bellatrix_config = BellatrixConfig(
            enable_fusion=True,
            enable_zero_copy=True
        )
        return BellatrixOptimizer(bellatrix_config)

    def migrate_to_capella(self) -> Any:
        """State transition to Capella Enhanced AI."""
        from .capella import CapellaOptimizer, CapellaConfig
        capella_config = CapellaConfig()
        return CapellaOptimizer(capella_config)


def create_phase0_optimizer(config: Optional[Phase0Config] = None, **kwargs) -> TransformerOptimizer:
    """Factory creating a Phase 0 optimizer instance."""
    if config is None:
        config = Phase0Config(**kwargs)
    return TransformerOptimizer(config)
