"""
Constraint-Based Hyperparameter Optimization

JuMP-based bounded optimization for loss functions.
"""

"""
    optimize_hyperparameters(loss_fn, bounds)

Optimize hyperparameters using JuMP for constraint-based optimization.
"""
function optimize_hyperparameters(
    loss_fn::Function,
    bounds::Vector{Tuple{Float64, Float64}}
)
    if isempty(bounds)
        throw(ArgumentError("bounds cannot be empty"))
    end
    
    for (i, (lb, ub)) in enumerate(bounds)
        if lb > ub
            throw(ArgumentError("Bounds for parameter $i: lower ($lb) > upper ($ub)"))
        end
    end
    
    model = Model(DEFAULT_SOLVER)
    n = length(bounds)
    
    @variable(model, bounds[i][1] <= x[i=1:n] <= bounds[i][2])
    @objective(model, Min, loss_fn(x))
    
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end
