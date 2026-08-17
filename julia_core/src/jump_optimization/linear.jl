"""
Linear Programming

Linear optimization solving via JuMP.
"""

"""
    create_linear_model(c, A, b, lb, ub, n)

Create a JuMP model for linear programming.
"""
function create_linear_model(
    c::Vector{Float64},
    A::Matrix{Float64},
    b::Vector{Float64},
    lb::Vector{Float64},
    ub::Vector{Float64},
    n::Int
)
    model = Model(DEFAULT_SOLVER)
    @variable(model, lb[i] <= x[i=1:n] <= ub[i])
    @constraint(model, A * x .<= b)
    @objective(model, Min, c' * x)
    return model, x
end

"""
    optimize_linear(c, A, b, lb, ub)

Solve linear programming problem: minimize c'*x subject to A*x <= b, lb <= x <= ub.
"""
function optimize_linear(
    c::Vector{Float64},
    A::Matrix{Float64},
    b::Vector{Float64},
    lb::Vector{Float64},
    ub::Vector{Float64}
)
    validate_linear_problem_dimensions(c, A, b, lb, ub)
    n = length(c)
    model, x = create_linear_model(c, A, b, lb, ub, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end
