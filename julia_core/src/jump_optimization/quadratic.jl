"""
Quadratic Programming

Quadratic optimization solving via JuMP.
"""

"""
    create_quadratic_model(Q, c, A, b, lb, ub, n)

Create a JuMP model for quadratic programming.
"""
function create_quadratic_model(
    Q::Matrix{Float64},
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
    @objective(model, Min, x' * Q * x + c' * x)
    return model, x
end

"""
    optimize_quadratic(Q, c, A, b, lb, ub)

Solve quadratic programming problem: minimize x'*Q*x + c'*x subject to A*x <= b, lb <= x <= ub.
"""
function optimize_quadratic(
    Q::Matrix{Float64},
    c::Vector{Float64},
    A::Matrix{Float64},
    b::Vector{Float64},
    lb::Vector{Float64},
    ub::Vector{Float64}
)
    n = validate_quadratic_inputs(Q, c, A, b, lb, ub)
    model, x = create_quadratic_model(Q, c, A, b, lb, ub, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end
