"""
Numerical Utilities

Softmax, Log-Softmax, GELU, Swish, Sigmoid, LayerNorm, and RMSNorm.
"""

"""
    softmax(x; dims=1)

Compute numerically stable softmax along specified dimension.
"""
function softmax(x::AbstractArray{T}; dims=1) where T
    max_x = maximum(x, dims=dims)
    exp_x = exp.(x .- max_x)
    return exp_x ./ (sum(exp_x, dims=dims) .+ eps(T))
end

"""
    log_softmax(x; dims=1)

Compute numerically stable log-softmax along specified dimension.
"""
function log_softmax(x::AbstractArray{T}; dims=1) where T
    max_x = maximum(x, dims=dims)
    shifted = x .- max_x
    log_sum_exp = log.(sum(exp.(shifted), dims=dims) .+ eps(T))
    return shifted .- log_sum_exp
end

"""
    gelu(x)

Gaussian Error Linear Unit (GELU) activation function.
"""
function gelu(x)
    return 0.5f0 .* x .* (1.0f0 .+ tanh.(SQRT_2_OVER_PI .* (x .+ GELU_APPROX_CONST .* x.^3)))
end

"""
    swish(x)

SiLU/Swish activation function.
"""
function swish(x)
    return x .* sigmoid.(x)
end

"""
    sigmoid(x)

Sigmoid activation function with numerical clamping.
"""
function sigmoid(x)
    x_clamped = clamp.(x, -500.0f0, 500.0f0)
    return 1.0f0 ./ (1.0f0 .+ exp.(-x_clamped))
end

"""
    layer_norm(x, γ, β; ε=1e-5)

Layer normalization with learnable scale (γ) and shift (β) parameters.
"""
function layer_norm(x::AbstractArray{T}, γ, β; ε::T = T(DEFAULT_EPSILON)) where T
    μ = mean(x, dims=ndims(x))
    σ² = var(x, dims=ndims(x), corrected=false)
    normalized = (x .- μ) ./ sqrt.(σ² .+ ε)
    return γ .* normalized .+ β
end

"""
    rms_norm(x, γ; ε=1e-5)

Root Mean Square (RMS) normalization.
"""
function rms_norm(x::AbstractArray{T}, γ; ε::T = T(DEFAULT_EPSILON)) where T
    rms = sqrt.(mean(x.^2, dims=ndims(x)) .+ ε)
    return γ .* x ./ rms
end
