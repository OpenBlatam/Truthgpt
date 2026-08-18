"""
Native TruthGPT Transformer Model Architecture
===============================================
Direct exports and aliases to native TruthGPT transformer architecture components.
"""

from __future__ import annotations

from .models import (
    TruthGPTModelConfig,
    TruthGPTConfig,
    TruthGPTPositionalEncoding,
    TruthGPTSelfAttention,
    TruthGPTFeedForward,
    TruthGPTMLP,
    TruthGPTTransformerLayer,
    TruthGPTBlock,
    TruthGPTOutput,
    TruthGPTModel,
    TruthGPTForCausalLM,
    create_truthgpt_model,
    load_truthgpt_model,
    save_truthgpt_model,
)

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
