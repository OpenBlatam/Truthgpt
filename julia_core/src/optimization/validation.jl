"""
Optimization Validation

Validation functions for hyperparameter bounds and optimization inputs.
"""

"""
    validate_lr_bounds(lr_min, lr_max)

Validate learning rate bounds.
"""
function validate_lr_bounds(lr_min::Float64, lr_max::Float64)
    if lr_min <= 0.0 || lr_max <= 0.0
        throw(ArgumentError("Learning rate bounds must be positive"))
    end
    if lr_min >= lr_max
        throw(ArgumentError("lr_min ($lr_min) must be < lr_max ($lr_max)"))
    end
end

"""
    validate_batch_bounds(batch_min, batch_max)

Validate batch size bounds.
"""
function validate_batch_bounds(batch_min::Int, batch_max::Int)
    if batch_min <= 0 || batch_max <= 0
        throw(ArgumentError("Batch size bounds must be positive"))
    end
    if batch_min > batch_max
        throw(ArgumentError("batch_min ($batch_min) must be <= batch_max ($batch_max)"))
    end
end

"""
    validate_dropout_bounds(dropout_min, dropout_max)

Validate dropout probability bounds.
"""
function validate_dropout_bounds(dropout_min::Float64, dropout_max::Float64)
    if dropout_min < 0.0 || dropout_max > 1.0
        throw(ArgumentError("Dropout bounds must be in [0, 1]"))
    end
    if dropout_min > dropout_max
        throw(ArgumentError("dropout_min ($dropout_min) must be <= dropout_max ($dropout_max)"))
    end
end

"""
    validate_warmup_bounds(warmup_min, warmup_max)

Validate warmup steps bounds.
"""
function validate_warmup_bounds(warmup_min::Int, warmup_max::Int)
    if warmup_min <= 0 || warmup_max <= 0
        throw(ArgumentError("Warmup bounds must be positive"))
    end
    if warmup_min > warmup_max
        throw(ArgumentError("warmup_min ($warmup_min) must be <= warmup_max ($warmup_max)"))
    end
end

"""
    validate_optimization_inputs(loss_fn, bounds, method, max_iters)

Validate inputs for hyperparameter optimization.
"""
function validate_optimization_inputs(
    loss_fn::Function,
    bounds::HyperparamBounds,
    method::Symbol,
    max_iters::Int
)
    if max_iters <= 0
        throw(ArgumentError("max_iters must be positive, got $max_iters"))
    end
    
    valid_methods = [METHOD_BAYESIAN, METHOD_RANDOM, METHOD_GRID]
    if method ∉ valid_methods
        throw(ArgumentError(
            "method must be one of $valid_methods, got :$method"
        ))
    end
end
