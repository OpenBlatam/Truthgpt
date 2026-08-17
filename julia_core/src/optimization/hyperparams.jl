"""
Hyperparameter Optimization Engine

Core search loop for hyperparameter optimization.
"""

"""
    optimize_hyperparams(loss_fn, bounds; method=:bayesian, max_iters=100, seed=42)

Optimize hyperparameters using specified method.

# Arguments
- `loss_fn`: Function that takes params dict and returns loss (Float64)
- `bounds`: HyperparamBounds struct defining search space
- `method`: Optimization method (`:bayesian`, `:random`, or `:grid`)
- `max_iters`: Maximum optimization iterations
- `seed`: Random seed for reproducibility

# Returns
- `OptimizationResult` with best parameters and optimization history
"""
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
