"""
Mixed-Integer Programming (MIP)

MIP problem construction and solving via JuMP.
"""

"""
    create_mip_model(c, A, b, integer_vars, n)

Create a JuMP model for mixed-integer programming.
"""
function create_mip_model(
    c::Vector{Float64},
    A::Matrix{Float64},
    b::Vector{Float64},
    integer_vars::Vector{Int},
    n::Int
)
    model = Model(DEFAULT_SOLVER)
    @variable(model, x[i=1:n] >= 0)
    set_integer_constraints!(model, x, integer_vars)
    @constraint(model, A * x .<= b)
    @objective(model, Min, c' * x)
    return model, x
end

"""
    optimize_mip(c, A, b, integer_vars)

Solve mixed-integer programming problem: minimize c'*x subject to A*x <= b, x >= 0 with integer variables.
"""
function optimize_mip(
    c::Vector{Float64},
    A::Matrix{Float64},
    b::Vector{Float64},
    integer_vars::Vector{Int}
)
    n = validate_mip_inputs(c, A, b, integer_vars)
    model, x = create_mip_model(c, A, b, integer_vars, n)
    optimize!(model)
    status = termination_status(model)
    return extract_solution(model, x, status)
end
