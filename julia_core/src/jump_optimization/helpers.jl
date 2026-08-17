"""
JuMP Optimization Helpers

Solution extraction and constraint setting helpers.
"""

"""
    extract_solution(model, x, status)

Extract solution and objective value from solved optimization model.
"""
function extract_solution(model::Model, x, status)
    if status == STATUS_OPTIMAL
        solution = value.(x)
        objective = objective_value(model)
        return solution, objective
    else
        error("Optimization failed with status: $status")
    end
end

"""
    set_integer_constraints!(model, x, integer_vars)

Set integer constraints on specified variables.
"""
function set_integer_constraints!(model::Model, x, integer_vars::Vector{Int})
    for idx in integer_vars
        set_integer(x[idx])
    end
end
