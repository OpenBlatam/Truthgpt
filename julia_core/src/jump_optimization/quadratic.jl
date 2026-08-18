"""
Quadratic Programming

Quadratic optimization solving via JuMP.
"""

"""
    create_quadratic_model(Q, c, A, b, lb, ub, n)

Create a JuMP model for quadratic programming.
"""
function create_quadratic_model(
    Q::AbstractMatrix{<:Real},
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real},
    n::Int
)
    Q_f64 = convert(Matrix{Float64}, Q)
    c_f64 = convert(Vector{Float64}, c)
    A_f64 = convert(Matrix{Float64}, A)
    b_f64 = convert(Vector{Float64}, b)
    lb_f64 = convert(Vector{Float64}, lb)
    ub_f64 = convert(Vector{Float64}, ub)

    model = Model(DEFAULT_SOLVER)
    @variable(model, lb_f64[i] <= x[i=1:n] <= ub_f64[i])
    @constraint(model, A_f64 * x .<= b_f64)
    @objective(model, Min, x' * Q_f64 * x + c_f64' * x)
    return model, x
end

"""
    optimize_quadratic(Q, c, A, b, lb, ub)

Solve quadratic programming problem: minimize x'*Q*x + c'*x subject to A*x <= b, lb <= x <= ub.
"""
function optimize_quadratic(
    Q::AbstractMatrix{<:Real},
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real}
)
    n = validate_quadratic_inputs(Q, c, A, b, lb, ub)
    model, x = create_quadratic_model(Q, c, A, b, lb, ub, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end

