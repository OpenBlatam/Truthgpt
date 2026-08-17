"""
Optimization Module

Mathematical Optimization for TruthGPT:
- Hyperparameter optimization (random, grid, bayesian)
- Loss functions (cross-entropy, focal loss)
- Learning rate scheduling (cosine, warmup)
- Gradient operations (clipping, accumulation)
"""

using LinearAlgebra
using Random
using Statistics

include("constants.jl")
include("types.jl")
include("validation.jl")
include("sampling.jl")
include("hyperparams.jl")
include("losses.jl")
include("schedulers.jl")
include("gradients.jl")

export HyperparamBounds, OptimizationResult
export optimize_hyperparams
export cross_entropy, focal_loss, softmax
export cosine_schedule, warmup_cosine_schedule, linear_warmup
export clip_grad_norm!, gradient_accumulate!
