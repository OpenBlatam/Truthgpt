"""
Optimization Types

Type definitions for hyperparameter bounds and optimization results.
"""

"""
    HyperparamBounds

Bounds for hyperparameter optimization with validation.

# Fields
- `lr_min`, `lr_max`: Learning rate bounds
- `batch_min`, `batch_max`: Batch size bounds
- `dropout_min`, `dropout_max`: Dropout probability bounds [0, 1]
- `warmup_min`, `warmup_max`: Warmup steps bounds
"""
struct HyperparamBounds
    lr_min::Float64
    lr_max::Float64
    batch_min::Int
    batch_max::Int
    dropout_min::Float64
    dropout_max::Float64
    warmup_min::Int
    warmup_max::Int
    
    function HyperparamBounds(
        lr_min::Float64,
        lr_max::Float64,
        batch_min::Int,
        batch_max::Int,
        dropout_min::Float64,
        dropout_max::Float64,
        warmup_min::Int,
        warmup_max::Int
    )
        validate_lr_bounds(lr_min, lr_max)
        validate_batch_bounds(batch_min, batch_max)
        validate_dropout_bounds(dropout_min, dropout_max)
        validate_warmup_bounds(warmup_min, warmup_max)
        
        new(lr_min, lr_max, batch_min, batch_max, dropout_min, dropout_max, warmup_min, warmup_max)
    end
end

"""
    HyperparamBounds(; kwargs...)

Create HyperparamBounds with keyword arguments and default ranges.
"""
function HyperparamBounds(;
    lr_range::Tuple{Real, Real} = (DEFAULT_LR_MIN, DEFAULT_LR_MAX),
    batch_range::Tuple{Integer, Integer} = (DEFAULT_BATCH_MIN, DEFAULT_BATCH_MAX),
    dropout_range::Tuple{Real, Real} = (DEFAULT_DROPOUT_MIN, DEFAULT_DROPOUT_MAX),
    warmup_range::Tuple{Integer, Integer} = (DEFAULT_WARMUP_MIN, DEFAULT_WARMUP_MAX)
)
    HyperparamBounds(
        Float64(lr_range[1]), Float64(lr_range[2]),
        Int(batch_range[1]), Int(batch_range[2]),
        Float64(dropout_range[1]), Float64(dropout_range[2]),
        Int(warmup_range[1]), Int(warmup_range[2])
    )
end


"""
    OptimizationResult

Result from hyperparameter optimization.

# Fields
- `best_params`: Dictionary of best hyperparameters found
- `best_loss`: Best loss value achieved
- `iterations`: Total number of iterations performed
- `history`: Vector of loss values at each iteration
"""
struct OptimizationResult
    best_params::Dict{Symbol, Any}
    best_loss::Float64
    iterations::Int
    history::Vector{Float64}
end
