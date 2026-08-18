"""
Linear Programming

Linear optimization solving via JuMP.
"""

"""
    create_linear_model(c, A, b, lb, ub, n)

Create a JuMP model for linear programming.
"""
function create_linear_model(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real},
    n::Int
)
    c_f64 = convert(Vector{Float64}, c)
    A_f64 = convert(Matrix{Float64}, A)
    b_f64 = convert(Vector{Float64}, b)
    lb_f64 = convert(Vector{Float64}, lb)
    ub_f64 = convert(Vector{Float64}, ub)

    model = Model(DEFAULT_SOLVER)
    @variable(model, lb_f64[i] <= x[i=1:n] <= ub_f64[i])
    @constraint(model, A_f64 * x .<= b_f64)
    @objective(model, Min, c_f64' * x)
    return model, x
end

"""
    optimize_linear(c, A, b, lb, ub)

Solve linear programming problem: minimize c'*x subject to A*x <= b, lb <= x <= ub.
"""
function optimize_linear(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real}
)
    validate_linear_problem_dimensions(c, A, b, lb, ub)
    n = length(c)
    model, x = create_linear_model(c, A, b, lb, ub, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end

