"""
Utils Module

Utility functions for TruthGPT Julia Core:
- Timing and profiling
- Memory management
- Data type conversion (Float32, Float16, BFloat16)
- Parallel computation
- Random number generation
- Numerical operations (softmax, activations, normalization)
"""

using Base.Threads
using Random
using Statistics

include("constants.jl")
include("timing.jl")
include("memory.jl")
include("conversion.jl")
include("parallel.jl")
include("random.jl")
include("numerical.jl")

export @timed_block, benchmark, format_time, format_bytes, memory_info
export to_float32, to_float16, to_bfloat16, from_bfloat16
export parallel_map, parallel_reduce
export random_normal, random_uniform, xavier_init, he_init
export softmax, log_softmax, gelu, swish, sigmoid, layer_norm, rms_norm
