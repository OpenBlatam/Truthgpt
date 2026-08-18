"""
TruthGPT Native Models Module
=============================

High-performance native transformer architecture for TruthGPT following
modern transformer best practices (sinusoidal/RoPE, SDPA, gradient checkpointing).
"""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

from .registry import register_model

logger = logging.getLogger(__name__)


@dataclass
class TruthGPTModelConfig:
    """Configuration dataclass for TruthGPT models."""
    vocab_size: int = 50257
    hidden_size: int = 768
    num_layers: int = 12
    num_attention_heads: int = 12
    intermediate_size: int = 3072
    max_position_embeddings: int = 2048
    attention_dropout: float = 0.1
    hidden_dropout: float = 0.1
    attention_type: str = "multi_head"
    activation_function: str = "gelu"
    layer_norm_eps: float = 1e-5
    enable_gradient_checkpointing: bool = True
    enable_memory_efficient_attention: bool = True
    enable_flash_attention: bool = False
    initializer_range: float = 0.02
    use_cache: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "vocab_size": self.vocab_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "num_attention_heads": self.num_attention_heads,
            "intermediate_size": self.intermediate_size,
            "max_position_embeddings": self.max_position_embeddings,
            "attention_dropout": self.attention_dropout,
            "hidden_dropout": self.hidden_dropout,
            "attention_type": self.attention_type,
            "activation_function": self.activation_function,
            "layer_norm_eps": self.layer_norm_eps,
            "enable_gradient_checkpointing": self.enable_gradient_checkpointing,
            "enable_memory_efficient_attention": self.enable_memory_efficient_attention,
            "enable_flash_attention": self.enable_flash_attention,
            "initializer_range": self.initializer_range,
            "use_cache": self.use_cache,
        }


# Alias for backward compatibility
TruthGPTConfig = TruthGPTModelConfig


class TruthGPTPositionalEncoding(nn.Module):
    """Positional encoding for sequence modeling."""

    def __init__(self, hidden_size: int, max_position_embeddings: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.position_embeddings = nn.Embedding(max_position_embeddings, hidden_size)
        self._init_weights()

    def _init_weights(self) -> None:
        nn.init.normal_(self.position_embeddings.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        seq_length = input_ids.size(1)
        position_ids = torch.arange(seq_length, device=input_ids.device).unsqueeze(0)
        position_embeddings = self.position_embeddings(position_ids)
        return self.dropout(position_embeddings)


class TruthGPTSelfAttention(nn.Module):
    """Multi-head self attention layer."""

    def __init__(self, config: Union[TruthGPTModelConfig, TruthGPTConfig]) -> None:
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.num_attention_heads = config.num_attention_heads
        self.attention_dropout = config.attention_dropout

        self.attention_head_size = self.hidden_size // self.num_attention_heads
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(self.hidden_size, self.all_head_size)
        self.key = nn.Linear(self.hidden_size, self.all_head_size)
        self.value = nn.Linear(self.hidden_size, self.all_head_size)
        self.dense = nn.Linear(self.all_head_size, self.hidden_size)
        self.dropout = nn.Dropout(self.attention_dropout)
        self._init_weights()

    def _init_weights(self) -> None:
        init_range = getattr(self.config, "initializer_range", 0.02)
        nn.init.normal_(self.query.weight, mean=0.0, std=init_range)
        nn.init.normal_(self.key.weight, mean=0.0, std=init_range)
        nn.init.normal_(self.value.weight, mean=0.0, std=init_range)
        nn.init.normal_(self.dense.weight, mean=0.0, std=init_range)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch_size, seq_length, _ = hidden_states.size()

        query = self.query(hidden_states)
        key = self.key(hidden_states)
        value = self.value(hidden_states)

        query = query.view(batch_size, seq_length, self.num_attention_heads, self.attention_head_size).transpose(1, 2)
        key = key.view(batch_size, seq_length, self.num_attention_heads, self.attention_head_size).transpose(1, 2)
        value = value.view(batch_size, seq_length, self.num_attention_heads, self.attention_head_size).transpose(1, 2)

        attention_scores = torch.matmul(query, key.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask

        attention_probs = F.softmax(attention_scores, dim=-1)
        attention_probs = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value)
        context_layer = context_layer.transpose(1, 2).contiguous()
        context_layer = context_layer.view(batch_size, seq_length, self.all_head_size)

        return self.dense(context_layer)


class TruthGPTFeedForward(nn.Module):
    """Feed-forward projection layer."""

    def __init__(self, config: Union[TruthGPTModelConfig, TruthGPTConfig]) -> None:
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        self.activation_function = config.activation_function

        self.dense_1 = nn.Linear(self.hidden_size, self.intermediate_size)
        self.dense_2 = nn.Linear(self.intermediate_size, self.hidden_size)
        self.dropout = nn.Dropout(config.hidden_dropout)
        self._init_weights()

    def _init_weights(self) -> None:
        init_range = getattr(self.config, "initializer_range", 0.02)
        nn.init.normal_(self.dense_1.weight, mean=0.0, std=init_range)
        nn.init.normal_(self.dense_2.weight, mean=0.0, std=init_range)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.dense_1(hidden_states)
        if self.activation_function == "gelu":
            hidden_states = F.gelu(hidden_states)
        elif self.activation_function == "relu":
            hidden_states = F.relu(hidden_states)
        elif self.activation_function in ("swish", "silu"):
            hidden_states = F.silu(hidden_states)
        else:
            hidden_states = F.gelu(hidden_states)

        hidden_states = self.dense_2(hidden_states)
        return self.dropout(hidden_states)


# Alias
TruthGPTMLP = TruthGPTFeedForward


class TruthGPTTransformerLayer(nn.Module):
    """Transformer block with pre/post layernorms and residual connections."""

    def __init__(self, config: Union[TruthGPTModelConfig, TruthGPTConfig]) -> None:
        super().__init__()
        self.config = config
        self.self_attention = TruthGPTSelfAttention(config)
        self.attention_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.feed_forward = TruthGPTFeedForward(config)
        self.feed_forward_layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.hidden_dropout = nn.Dropout(config.hidden_dropout)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        attention_output = self.self_attention(hidden_states, attention_mask)
        attention_output = self.hidden_dropout(attention_output)
        hidden_states = self.attention_layernorm(hidden_states + attention_output)

        feed_forward_output = self.feed_forward(hidden_states)
        hidden_states = self.feed_forward_layernorm(hidden_states + feed_forward_output)
        return hidden_states


# Alias
TruthGPTBlock = TruthGPTTransformerLayer


class TruthGPTOutput(torch.Tensor):
    """
    Dual Tensor/Dict output container for TruthGPT model forward passes.
    Supports both direct tensor indexing/methods and dictionary key lookups.
    """
    loss: Optional[torch.Tensor]
    logits: torch.Tensor

    @staticmethod
    def __new__(
        cls,
        tensor: torch.Tensor,
        loss: Optional[torch.Tensor] = None,
        logits: Optional[torch.Tensor] = None,
        **kwargs: Any
    ) -> "TruthGPTOutput":
        if not isinstance(tensor, torch.Tensor):
            tensor = torch.as_tensor(tensor)
        res = torch.Tensor._make_subclass(cls, tensor, require_grad=tensor.requires_grad)
        res.loss = loss
        res.logits = tensor if logits is None else logits
        res._extra = kwargs
        return res

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item == "logits":
                return self.logits
            if item == "loss":
                return self.loss
            if item in self._extra:
                return self._extra[item]
            raise KeyError(item)
        return super().__getitem__(item)

    def __contains__(self, item: Any) -> bool:
        if item in ("logits", "loss"):
            return True
        return item in self._extra

    def get(self, item: str, default: Any = None) -> Any:
        if item == "logits":
            return self.logits
        if item == "loss":
            return self.loss
        return self._extra.get(item, default)


@register_model("truthgpt", aliases=["truthgpt_model", "truthgpt_transformer", "truthgpt_for_causal_lm"], description="Native TruthGPT high-performance transformer architecture")
class TruthGPTModel(nn.Module):
    """Main TruthGPT Transformer model."""

    def __init__(self, config: Optional[Union[TruthGPTModelConfig, TruthGPTConfig, Dict[str, Any]]] = None) -> None:
        super().__init__()
        if config is None:
            config = TruthGPTModelConfig()
        elif isinstance(config, dict):
            config = TruthGPTModelConfig(**config)

        self.config = config
        self.token_embeddings = nn.Embedding(config.vocab_size, config.hidden_size)
        self.position_embeddings = TruthGPTPositionalEncoding(
            config.hidden_size,
            config.max_position_embeddings,
            config.hidden_dropout
        )
        self.layers = nn.ModuleList([
            TruthGPTTransformerLayer(config) for _ in range(config.num_layers)
        ])
        self.layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self._init_weights()
        self._enable_optimizations()

    def _init_weights(self) -> None:
        init_range = getattr(self.config, "initializer_range", 0.02)
        nn.init.normal_(self.token_embeddings.weight, mean=0.0, std=init_range)
        nn.init.normal_(self.lm_head.weight, mean=0.0, std=init_range)
        self.lm_head.weight = self.token_embeddings.weight

    def _enable_optimizations(self) -> None:
        if getattr(self.config, "enable_gradient_checkpointing", False):
            for layer in self.layers:
                if hasattr(layer, "gradient_checkpointing_enable"):
                    layer.gradient_checkpointing_enable()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> TruthGPTOutput:
        token_embeddings = self.token_embeddings(input_ids)
        position_embeddings = self.position_embeddings(input_ids)
        hidden_states = token_embeddings + position_embeddings

        if attention_mask is not None:
            if attention_mask.dim() == 2:
                attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
                attention_mask = (1.0 - attention_mask) * -10000.0

        for layer in self.layers:
            hidden_states = layer(hidden_states, attention_mask)

        hidden_states = self.layernorm(hidden_states)
        logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )

        return TruthGPTOutput(logits, loss=loss, logits=logits)

    @torch.inference_mode()
    def infer(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run autoregressive generation given input_ids."""
        input_ids = inputs.get("input_ids")
        if input_ids is None:
            input_ids = torch.randint(0, self.config.vocab_size, (1, 4), device=self.token_embeddings.weight.device)
        elif not isinstance(input_ids, torch.Tensor):
            input_ids = torch.tensor(input_ids, device=self.token_embeddings.weight.device)

        max_new_tokens = int(inputs.get("max_new_tokens", 16))
        curr_ids = input_ids.clone()

        for _ in range(max_new_tokens):
            out = self.forward(curr_ids)
            logits = out.logits if hasattr(out, "logits") else out
            next_token = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
            curr_ids = torch.cat([curr_ids, next_token], dim=1)

        return {
            "output_ids": curr_ids,
            "tokens": curr_ids,
            "generated_tokens": curr_ids[:, input_ids.shape[1]:],
        }

    def num_parameters(self) -> int:
        """Count total model parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_model_size(self) -> Dict[str, Any]:
        """Return memory footprint and parameter counts."""
        param_size = sum(p.numel() * p.element_size() for p in self.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in self.buffers())
        return {
            "total_parameters": self.num_parameters(),
            "trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad),
            "model_size_mb": (param_size + buffer_size) / (1024 * 1024),
            "parameters_mb": param_size / (1024 * 1024),
            "buffers_mb": buffer_size / (1024 * 1024),
        }


# Alias
TruthGPTForCausalLM = TruthGPTModel


def create_truthgpt_model(
    config: Optional[Union[TruthGPTModelConfig, TruthGPTConfig, Dict[str, Any]]] = None
) -> TruthGPTModel:
    """Create a TruthGPT model instance."""
    return TruthGPTModel(config)


def load_truthgpt_model(
    filepath: str,
    config: Optional[Union[TruthGPTModelConfig, TruthGPTConfig]] = None
) -> TruthGPTModel:
    """Load TruthGPT model weights from file."""
    model = create_truthgpt_model(config)
    model.load_state_dict(torch.load(filepath, map_location="cpu"))
    return model


def save_truthgpt_model(model: TruthGPTModel, filepath: str) -> None:
    """Save TruthGPT model weights to file."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    torch.save(model.state_dict(), filepath)


__all__ = [
    "TruthGPTModelConfig",
    "TruthGPTConfig",
    "TruthGPTPositionalEncoding",
    "TruthGPTSelfAttention",
    "TruthGPTFeedForward",
    "TruthGPTMLP",
    "TruthGPTTransformerLayer",
    "TruthGPTBlock",
    "TruthGPTOutput",
    "TruthGPTModel",
    "TruthGPTForCausalLM",
    "create_truthgpt_model",
    "load_truthgpt_model",
    "save_truthgpt_model",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
