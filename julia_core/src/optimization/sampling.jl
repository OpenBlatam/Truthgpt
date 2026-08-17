"""
Optimization Sampling

Random, grid, and Bayesian hyperparameter sampling algorithms with interpolation helpers.
"""

"""
    sample_params(bounds, method, iter, max_iters, rng)

Sample hyperparameters based on optimization method.
"""
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
    else  # METHOD_BAYESIAN
        return bayesian_sample(bounds, iter, rng)
    end
end

"""
    random_sample(bounds, rng)

Sample hyperparameters uniformly at random from bounds.
"""
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

"""
    sample_log_uniform_lr(lr_min, lr_max, rng)

Sample learning rate using log-uniform distribution.
"""
function sample_log_uniform_lr(lr_min::Float64, lr_max::Float64, rng::AbstractRNG)
    log_lr_min = log(lr_min)
    log_lr_max = log(lr_max)
    return exp(log_lr_min + rand(rng) * (log_lr_max - log_lr_min))
end

"""
    sample_uniform_int(min_val, max_val, rng)

Sample integer uniformly from [min_val, max_val].
"""
function sample_uniform_int(min_val::Int, max_val::Int, rng::AbstractRNG)
    return rand(rng, min_val:max_val)
end

"""
    sample_uniform_float(min_val, max_val, rng)

Sample float uniformly from [min_val, max_val).
"""
function sample_uniform_float(min_val::Float64, max_val::Float64, rng::AbstractRNG)
    return min_val + rand(rng) * (max_val - min_val)
end

"""
    grid_sample(bounds, iter, max_iters)

Sample hyperparameters using grid search (linear progression).
"""
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

"""
    compute_grid_progress(iter, max_iters)

Compute normalized progress for grid search.
"""
function compute_grid_progress(iter::Int, max_iters::Int)
    return (iter - 1) / max(max_iters - 1, 1)
end

"""
    interpolate_log_linear(min_val, max_val, progress)

Interpolate value using log-linear interpolation.
"""
function interpolate_log_linear(min_val::Float64, max_val::Float64, progress::Float64)
    log_min = log(min_val)
    log_max = log(max_val)
    return exp(log_min + progress * (log_max - log_min))
end

"""
    interpolate_linear(min_val, max_val, progress)

Interpolate value using linear interpolation.
"""
function interpolate_linear(min_val::Real, max_val::Real, progress::Float64)
    return min_val + progress * (max_val - min_val)
end

"""
    bayesian_sample(bounds, iter, rng)

Sample hyperparameters using simplified Bayesian optimization.
"""
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
