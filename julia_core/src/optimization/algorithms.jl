"""
Hyperparameter Optimization Algorithms & Loss Functions
"""

using Random
using LinearAlgebra
using Statistics

function optimize_hyperparams(
    loss_fn::Function,
    bounds::HyperparamBounds;
    method::Symbol = METHOD_BAYESIAN,
    max_iters::Int = 100,
    seed::Int = 42
)
    validate_optimization_inputs(loss_fn, bounds, method, max_iters)
    rng = MersenneTwister(seed)
    best_loss = Inf
    best_params = Dict{Symbol, Any}()
    history = Vector{Float64}(undef, max_iters)
    
    for iteration in 1:max_iters
        params = sample_params(bounds, method, iteration, max_iters, rng)
        try
            loss = loss_fn(params)
            if !isfinite(loss)
                @warn "Iteration $iteration produced non-finite loss: $loss"
                history[iteration] = Inf
                continue
            end
            history[iteration] = loss
            if loss < best_loss
                best_loss = loss
                best_params = copy(params)
                @info "New best at iteration $iteration: loss=$(round(loss, digits=6))"
            end
        catch e
            @warn "Iteration $iteration failed: $e"
            history[iteration] = Inf
        end
    end
    
    if best_loss == Inf
        throw(ErrorException("Optimization failed: no valid loss values found"))
    end
    
    return OptimizationResult(best_params, best_loss, max_iters, history)
end

function sample_params(
    bounds::HyperparamBounds,
    method::Symbol,
    iter::Int,
    max_iters::Int,
    rng::AbstractRNG
)
    if method == METHOD_RANDOM
        return random_sample(bounds, rng)
    elseif method == METHOD_GRID
        return grid_sample(bounds, iter, max_iters)
    else
        return bayesian_sample(bounds, iter, rng)
    end
end

function random_sample(bounds::HyperparamBounds, rng::AbstractRNG)
    lr = sample_log_uniform_lr(bounds.lr_min, bounds.lr_max, rng)
    batch_size = sample_uniform_int(bounds.batch_min, bounds.batch_max, rng)
    dropout = sample_uniform_float(bounds.dropout_min, bounds.dropout_max, rng)
    warmup_steps = sample_uniform_int(bounds.warmup_min, bounds.warmup_max, rng)
    
    return Dict{Symbol, Any}(
        :lr => lr,
        :batch_size => batch_size,
        :dropout => dropout,
        :warmup_steps => warmup_steps
    )
end

function sample_log_uniform_lr(lr_min::Float64, lr_max::Float64, rng::AbstractRNG)
    log_lr_min = log(lr_min)
    log_lr_max = log(lr_max)
    return exp(log_lr_min + rand(rng) * (log_lr_max - log_lr_min))
end

function sample_uniform_int(min_val::Int, max_val::Int, rng::AbstractRNG)
    return rand(rng, min_val:max_val)
end

function sample_uniform_float(min_val::Float64, max_val::Float64, rng::AbstractRNG)
    return min_val + rand(rng) * (max_val - min_val)
end

function grid_sample(bounds::HyperparamBounds, iter::Int, max_iters::Int)
    progress = compute_grid_progress(iter, max_iters)
    lr = interpolate_log_linear(bounds.lr_min, bounds.lr_max, progress)
    batch_size = round(Int, interpolate_linear(bounds.batch_min, bounds.batch_max, progress))
    dropout = interpolate_linear(bounds.dropout_min, bounds.dropout_max, progress)
    warmup_steps = round(Int, interpolate_linear(bounds.warmup_min, bounds.warmup_max, progress))
    
    return Dict{Symbol, Any}(
        :lr => lr,
        :batch_size => batch_size,
        :dropout => dropout,
        :warmup_steps => warmup_steps
    )
end

function compute_grid_progress(iter::Int, max_iters::Int)
    return (iter - 1) / max(max_iters - 1, 1)
end

function interpolate_log_linear(min_val::Float64, max_val::Float64, progress::Float64)
    log_min = log(min_val)
    log_max = log(max_val)
    return exp(log_min + progress * (log_max - log_min))
end

function interpolate_linear(min_val::Real, max_val::Real, progress::Float64)
    return min_val + progress * (max_val - min_val)
end

function bayesian_sample(bounds::HyperparamBounds, iter::Int, rng::AbstractRNG)
    exploration_prob = max(
        DEFAULT_BAYESIAN_MIN_EXPLORATION,
        1.0 - iter * DEFAULT_BAYESIAN_EXPLORATION_DECAY
    )
    if rand(rng) < exploration_prob
        return random_sample(bounds, rng)
    else
        return random_sample(bounds, rng)
    end
end

function cross_entropy(logits::AbstractMatrix{T}, targets::AbstractVector{<:Integer}) where T
    n_classes, batch_size = size(logits)
    if length(targets) != batch_size
        throw(DimensionMismatch("targets length $(length(targets)) must match batch_size $batch_size"))
    end
    if any(t -> t < 1 || t > n_classes, targets)
        throw(ArgumentError("Target indices must be in [1, $n_classes]"))
    end
    
    max_logits = maximum(logits, dims=1)
    shifted = logits .- max_logits
    log_sum_exp = log.(sum(exp.(shifted), dims=1) .+ eps(T))
    log_probs = shifted .- log_sum_exp
    
    loss = zero(T)
    @inbounds @simd for i in 1:batch_size
        loss -= log_probs[targets[i], i]
    end
    return loss / batch_size
end

function focal_loss(
    logits::AbstractMatrix{T},
    targets::AbstractVector{<:Integer};
    gamma::T = T(DEFAULT_FOCAL_GAMMA),
    alpha::T = T(DEFAULT_FOCAL_ALPHA)
) where T
    n_classes, batch_size = size(logits)
    if length(targets) != batch_size
        throw(DimensionMismatch("targets length $(length(targets)) must match batch_size $batch_size"))
    end
    if any(t -> t < 1 || t > n_classes, targets)
        throw(ArgumentError("Target indices must be in [1, $n_classes]"))
    end
    if gamma < 0.0
        throw(ArgumentError("gamma must be non-negative, got $gamma"))
    end
    if alpha < 0.0 || alpha > 1.0
        throw(ArgumentError("alpha must be in [0, 1], got $alpha"))
    end
    
    probs = softmax(logits)
    loss = zero(T)
    eps_val = eps(T)
    
    @inbounds @simd for i in 1:batch_size
        p = probs[targets[i], i]
        p = max(eps_val, min(1.0 - eps_val, p))
        focal_weight = (1.0 - p)^gamma
        loss -= alpha * focal_weight * log(p)
    end
    return loss / batch_size
end

function softmax(x::AbstractArray{T}; dims=1) where T
    max_x = maximum(x, dims=dims)
    exp_x = exp.(x .- max_x)
    exp_x ./ (sum(exp_x, dims=dims) .+ eps(T))
end
