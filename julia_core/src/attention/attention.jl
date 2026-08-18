"""
Attention Module

High-Performance Attention Mechanisms using native parallelism and SIMD.
Exports AttentionConfig, MultiHeadAttention, RoPE, standard and Flash Attention.
"""

using LinearAlgebra
using Random

include("constants.jl")
include("types.jl")
include("validation.jl")
include("kernels.jl")
include("standard.jl")
include("flash.jl")
include("multihead.jl")
include("rope.jl")

export AttentionConfig, AttentionOutput, d_model, scale
export attention_forward, flash_attention
export MultiHeadAttention, forward
export RoPE, apply_rope!
