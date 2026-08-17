"""
GPU Acceleration Submodule

Provides GPU computing acceleration using CUDA.jl when available.
"""

include("cuda.jl")

export has_cuda, attention_cuda, batched_mul_cuda
