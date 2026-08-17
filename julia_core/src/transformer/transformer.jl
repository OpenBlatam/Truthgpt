"""
Transformer Submodule

Native Julia transformer implementation featuring RoPE, SwiGLU, pre-norm architecture,
causal attention masking, and nucleus token generation.
"""

using LinearAlgebra
using Statistics
using Random

include("types.jl")
include("rope.jl")
include("layers.jl")
include("model.jl")
include("generation.jl")

export TransformerConfig, Transformer, MultiHeadAttention, FeedForward
export TransformerBlock, generate, create_causal_mask
export precompute_rope_freqs, apply_rope
