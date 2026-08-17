"""
TruthGPT.jl - High-Performance Scientific Computing & Deep Learning Backend

Julia module providing superior numerical performance, automatic differentiation,
and accelerated linear algebra routines for the TruthGPT platform.

## Submodules
- `Attention`: Multi-head and Flash attention kernels with RoPE support.
- `Cache`: Lock-free and sharded KV caching with adaptive eviction.
- `Compression`: High-throughput LZ4 and Zstandard compression.
- `Inference`: Fast stochastic and nucleus token sampling.
- `GPU`: CUDA-accelerated kernels.
- `Optimization`: Hyperparameter optimization, loss functions, and schedulers.
- `Transformer`: Pre-norm Transformer architecture with SwiGLU FFN.
- `Quantization`: INT8, INT4, and grouped block quantization.
- `FluxML`: Flux.jl deep learning and gradient training pipelines.
- `JuMPOptimization`: Mathematical programming and constraint optimization via JuMP.
- `Utils`: Profiling, memory tracking, type conversions, activations, and parallel utilities.
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

module Compression
    include("compression/compression.jl")
end

module Inference
    include("inference/inference.jl")
end

module GPU
    include("gpu/gpu.jl")
end

module Optimization
    include("optimization/optimization.jl")
end

module Transformer
    include("transformer/transformer.jl")
end

module Quantization
    include("quantization/quantization.jl")
end

module FluxML
    include("flux_ml/flux_ml.jl")
end

module JuMPOptimization
    include("jump_optimization/jump_optimization.jl")
end

# Re-export submodules
export Utils, Attention, Cache, Compression, Inference, GPU
export Optimization, Transformer, Quantization, FluxML, JuMPOptimization

const VERSION = "1.0.0"

function __init__()
    @info "TruthGPT.jl v$VERSION initialized"
end

end # module TruthGPT
