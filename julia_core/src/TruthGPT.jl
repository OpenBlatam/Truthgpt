"""
TruthGPT.jl - High-Performance Scientific Computing Backend
============================================================

Root package module matching Project.toml [name = TruthGPT].
Re-exports TruthGPTCore and all submodules.
"""
module TruthGPT

include("TruthGPTCore.jl")

using .TruthGPTCore

# Re-export submodules
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

# Backward-compatibility aliases
export quantize_tensor, dequantize_tensor, create_transformer

const VERSION = TruthGPTCore.VERSION

end # module TruthGPT
