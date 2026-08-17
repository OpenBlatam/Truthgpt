"""
TruthGPT Julia Core
==================

High-performance scientific computing module for TruthGPT.

## Features
- JuMP-based mathematical optimization
- Flux.jl deep learning with automatic differentiation
- Attention mechanisms (Standard, Flash Attention, RoPE)
- Concurrent KV cache (single & sharded with LRU, LFU, FIFO, Adaptive eviction)
- Int4, Int8, and Grouped Quantization
- Pre-norm Transformer architectures
- CUDA GPU acceleration
- Zero-copy Python interoperability via PyCall / PyJulia
"""
module TruthGPTCore

using LinearAlgebra
using Statistics
using Random

const VERSION = "0.1.0"

# Include modular subsystems
include("utils/utils.jl")
include("optimization/optimization.jl")
include("attention/attention.jl")
include("quantization/quantization.jl")
include("cache/cache.jl")
include("flux_ml/flux_ml.jl")
include("jump_optimization/jump_optimization.jl")
include("transformer/transformer.jl")

# Helper for creating transformer matching polyglot signature
function create_transformer(d_model::Int=768, n_heads::Int=12, d_ff::Int=3072; n_layers::Int=12, vocab_size::Int=32000)
    config = TransformerConfig(
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        d_ff=d_ff,
        vocab_size=vocab_size
    )
    return Transformer(config)
end

# Re-export key functions and types for Python interop
export VERSION

# Optimization exports
export HyperparamBounds, OptimizationResult, optimize_hyperparams
export cross_entropy, focal_loss, cosine_schedule, warmup_cosine_schedule, linear_warmup
export clip_grad_norm!, gradient_accumulate!

# Attention exports
export AttentionConfig, d_model, scale
export attention_forward, flash_attention
export MultiHeadAttention, RoPE, apply_rope!

# Quantization exports
export quantize_tensor, dequantize_tensor

# Cache exports
export EvictionStrategy, LRU, LFU, FIFO, Adaptive
export CacheConfig, KVCache, ShardedKVCache
export kv_cache_get, kv_cache_put, clear!, hit_rate, stats

# Transformer exports
export TransformerConfig, Transformer, TransformerBlock, FeedForward
export create_transformer, generate, create_causal_mask

# Utils exports
export to_float32, to_float16, to_bfloat16, from_bfloat16
export parallel_map, parallel_reduce
export random_normal, random_uniform, xavier_init, he_init
export softmax, log_softmax, gelu, swish, sigmoid, layer_norm, rms_norm
export benchmark, format_time, format_bytes, memory_info

function __init__()
    @info "TruthGPTCore v$VERSION initialized"
end

end # module TruthGPTCore
