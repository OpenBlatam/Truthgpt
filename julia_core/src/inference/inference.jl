"""
Inference Submodule

High-performance inference sampling and decoding utilities.
"""

include("types.jl")
include("samplers.jl")

export TokenSampler, sample_greedy, sample_topk, sample_topp, sample_nucleus
export GenerationConfig, softmax!
