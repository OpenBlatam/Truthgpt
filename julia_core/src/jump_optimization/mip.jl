"""
Mixed-Integer Programming (MIP)

MIP problem construction and solving via JuMP.
"""

"""
    create_mip_model(c, A, b, integer_vars, n)

Create a JuMP model for mixed-integer programming.
"""
function create_mip_model(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    integer_vars::AbstractVector{<:Integer},
    n::Int
)
    c_f64 = convert(Vector{Float64}, c)
    A_f64 = convert(Matrix{Float64}, A)
    b_f64 = convert(Vector{Float64}, b)
    int_vars_vec = convert(Vector{Int}, integer_vars)

    model = Model(DEFAULT_SOLVER)
    @variable(model, x[i=1:n] >= 0)
    set_integer_constraints!(model, x, int_vars_vec)
    @constraint(model, A_f64 * x .<= b_f64)
    @objective(model, Min, c_f64' * x)
    return model, x
end

"""
    optimize_mip(c, A, b, integer_vars)

Solve mixed-integer programming problem: minimize c'*x subject to A*x <= b, x >= 0 with integer variables.
"""
function optimize_mip(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    integer_vars::AbstractVector{<:Integer}
)
    n = validate_mip_inputs(c, A, b, integer_vars)
    int_vars_vec = convert(Vector{Int}, integer_vars)
    model, x = create_mip_model(c, A, b, int_vars_vec, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end

