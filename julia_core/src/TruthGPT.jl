"""
TruthGPT.jl - High-Performance Scientific Computing Backend
============================================================

Root package module matching Project.toml [name = TruthGPT].
Contains modular submodules:
- Utils: timing, memory, conversion, parallel, random, and numerical operations
- Attention: standard attention, flash attention, multi-head attention, RoPE
- Cache: single & sharded concurrent KV cache with LRU/LFU/FIFO/Adaptive eviction
- Quantization: Int8, Int4, and grouped tensor quantization with calibration
- Optimization: hyperparameter optimization, loss functions, schedulers, gradients
- JumpOptimization: LP, QP, MIP mathematical optimization via JuMP
- FluxML: deep learning training, validation, losses, and prediction via Flux
- Transformer: complete pre-norm transformer model with SwiGLU & generation
- Compression: fast LZ4 and Zstd compression
- Inference: token sampling and nucleus filtering
- GPU: CUDA GPU acceleration kernels
"""
module TruthGPT

using LinearAlgebra
using Statistics
using Random

module Utils
include("utils/utils.jl")
end

module Attention
include("attention/attention.jl")
end

module Cache
include("cache/cache.jl")
end

module Quantization
include("quantization/quantization.jl")
end

module Optimization
include("optimization/optimization.jl")
end

module JumpOptimization
include("jump_optimization/jump_optimization.jl")
end

module FluxML
include("flux_ml/flux_ml.jl")
end

module Transformer
include("transformer/transformer.jl")
end

module Compression
include("compression/compression.jl")
end

module Inference
include("inference/inference.jl")
end

module GPU
include("gpu/gpu.jl")
end

const JuMPOptimization = JumpOptimization

export Utils, Attention, Cache, Quantization, Optimization, JumpOptimization, JuMPOptimization, FluxML, Transformer, Compression, Inference, GPU

# Re-export submodules into top-level namespace
using .Utils
using .Attention
using .Cache
using .Quantization
using .Optimization
using .JumpOptimization
using .FluxML
using .Transformer
using .Compression
using .Inference
using .GPU

# Attention Exports
export AttentionConfig, AttentionOutput, d_model, scale
export attention_forward, flash_attention, MultiHeadAttention, RoPE, apply_rope!

# Cache Exports
export EvictionStrategy, LRU, LFU, FIFO, Adaptive
export CacheConfig, CacheEntry, KVCache, ShardedKVCache
export kv_cache_get, kv_cache_put, clear!, hit_rate, stats

# Compression Exports
export compress_lz4, decompress_lz4, compress_zstd, decompress_zstd, CompressionStats

# Quantization Exports
export QuantParams, QuantizedTensor, QuantizedInt4, QuantizedGrouped, GroupQuantParams
export quantize_int8, quantize_int4, quantize_grouped, dequantize
export matmul_int8, dot_int8, Calibrator, observe!, get_params

# Optimization Exports
export HyperparamBounds, OptimizationResult, optimize_hyperparams
export cross_entropy, focal_loss
export cosine_schedule, warmup_cosine_schedule, linear_warmup
export clip_grad_norm!, gradient_accumulate!

# JuMP Optimization Exports
export optimize_linear, optimize_quadratic, optimize_mip, optimize_hyperparameters

# Flux ML Exports
export create_model, train_model, predict, create_language_model, train_language_model
export TrainingConfig, is_gpu_available

# Transformer Exports
export TransformerConfig, Transformer, FeedForward, TransformerBlock, generate, create_causal_mask

# Inference Exports
export TokenSampler, sample_greedy, sample_topk, sample_topp, sample_nucleus, GenerationConfig

# GPU Exports
export has_cuda, attention_cuda, batched_mul_cuda

# Utils Exports
export @timed_block, benchmark, format_time, format_bytes, memory_info
export to_float32, to_float16, to_bfloat16, from_bfloat16
export parallel_map, parallel_reduce
export random_normal, random_uniform, xavier_init, he_init
export softmax, log_softmax, gelu, swish, sigmoid, layer_norm, rms_norm

# Backward-compatibility wrappers
function create_transformer(d_model::Int=768, n_heads::Int=12, d_ff::Int=3072; n_layers::Int=12, vocab_size::Int=32000, kwargs...)
    config = TransformerConfig(d_model=d_model, n_heads=n_heads, n_layers=n_layers, d_ff=d_ff, vocab_size=vocab_size; kwargs...)
    return Transformer(config)
end

function quantize_tensor(tensor::AbstractArray; bits::Int=8, symmetric::Bool=true)
    if bits == 4
        return quantize_int4(to_float32(tensor))
    else
        return quantize_int8(to_float32(tensor), symmetric=symmetric)
    end
end

function dequantize_tensor(qtensor)
    return dequantize(qtensor)
end

export quantize_tensor, dequantize_tensor, create_transformer

const VERSION = "1.0.0"

function __init__()
    @info "TruthGPT.jl v$VERSION initialized"
end

end # module TruthGPT
