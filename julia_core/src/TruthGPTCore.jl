"""
TruthGPT Julia Core (TruthGPTCore)
===================================

High-performance scientific computing and machine learning core for TruthGPT.

## Features
- **Attention**: Scaled dot-product, Flash Attention, Multi-Head Attention, RoPE
- **Cache**: Thread-safe KV Cache with LRU, LFU, FIFO, and Adaptive eviction strategies + Sharding
- **Compression**: High-throughput LZ4 and Zstd block compression
- **Quantization**: High-speed INT8, INT4 (packed), and Grouped Quantization with calibration
- **Optimization**: Hyperparameter optimization (Bayesian, Random, Grid), Loss functions, Schedulers, Gradient clipping
- **JuMP Optimization**: LP, QP, MIP mathematical programming with HiGHS solver
- **FluxML**: Deep learning with native Julia autodiff, GPU support via CUDA.jl, LSTM language models
- **Transformer**: Full pre-norm transformer with RoPE, SwiGLU, causal masking, and nucleus token generation
- **Inference**: Token sampling (greedy, top-k, top-p, nucleus)
- **GPU**: CUDA kernel acceleration
- **Utils**: High-resolution benchmarking, memory profiling, Float32/Float16/BFloat16 conversion, parallel map/reduce

## Interoperability
- Native Julia module with submodules
- Zero-overhead Python interoperability via PyJulia (`from julia import TruthGPTCore`)
"""
module TruthGPTCore

using LinearAlgebra
using Statistics
using Random
using JSON3
using CodecLz4
using CodecZstd
using DataStructures
using JuMP
using HiGHS
using Flux
using CUDA
using LoopVectorization
using Base.Threads

const VERSION = "1.0.0"

# ═══════════════════════════════════════════════════════════════════════════════
# SUBMODULE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

module Utils
    using LinearAlgebra
    using Statistics
    using Random
    using Base.Threads
    include("utils/utils.jl")
end

module Attention
    using LinearAlgebra
    using Statistics
    using Random
    using LoopVectorization
    include("attention/attention.jl")
end

module Cache
    using Base.Threads
    using Random
    using DataStructures
    include("cache/cache.jl")
end

module Compression
    using CodecLz4
    using CodecZstd
    include("compression/compression.jl")
end

module Quantization
    using LinearAlgebra
    using Statistics
    include("quantization/quantization.jl")
end

module Optimization
    using LinearAlgebra
    using Statistics
    using Random
    include("optimization/optimization.jl")
end

module JumpOptimization
    using JuMP
    using HiGHS
    include("jump_optimization/constants.jl")
    include("jump_optimization/validation.jl")
    include("jump_optimization/helpers.jl")
    include("jump_optimization/linear.jl")
    include("jump_optimization/quadratic.jl")
    include("jump_optimization/mip.jl")
    include("jump_optimization/hyperparams.jl")
    export optimize_linear, optimize_quadratic, optimize_mip, optimize_hyperparameters
end

module FluxML
    using Flux
    using CUDA
    using Statistics
    include("flux_ml/flux_ml.jl")
end

module Transformer
    include("transformer/transformer.jl")
end

module Inference
    using Random
    include("inference/inference.jl")
end

module GPU
    using CUDA
    include("gpu/gpu.jl")
end

# ═══════════════════════════════════════════════════════════════════════════════
# TOP-LEVEL RE-EXPORTS (FOR PYTHON FFI & CONVENIENT JULIA ACCESS)
# ═══════════════════════════════════════════════════════════════════════════════

using .Utils
using .Attention
using .Cache
using .Compression
using .Quantization
using .Optimization
using .JumpOptimization
using .FluxML
using .Transformer
using .Inference
using .GPU

# Export submodules
export Utils, Attention, Cache, Compression, Quantization, Optimization, JumpOptimization, FluxML, Transformer, Inference, GPU

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

# Backward-Compatibility Aliases & Polyglot Helpers
const quantize_tensor = quantize_int8
const dequantize_tensor = dequantize
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
export quantize_tensor, dequantize_tensor, create_transformer

function __init__()
    @info "TruthGPTCore v$VERSION initialized"
end

end # module TruthGPTCore
