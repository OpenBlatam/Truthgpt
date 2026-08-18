"""
JuMP Optimization Validation

Input dimension, symmetry, bounds, and variable type validation.
"""

"""
    validate_linear_problem_dimensions(c, A, b, lb, ub)

Validate dimensions for linear programming problem.
"""
function validate_linear_problem_dimensions(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real}
)
    n = length(c)
    
    if n == 0
        throw(ArgumentError("Objective vector c cannot be empty"))
    end
    
    if size(A, 2) != n
        throw(DimensionMismatch(
            "Constraint matrix A must have $n columns, got $(size(A, 2))"
        ))
    end
    
    m = size(A, 1)
    if length(b) != m
        throw(DimensionMismatch(
            "Constraint vector b length $(length(b)) must match A rows $m"
        ))
    end
    
    if length(lb) != n
        throw(DimensionMismatch(
            "Lower bounds lb must have length $n, got $(length(lb))"
        ))
    end
    
    if length(ub) != n
        throw(DimensionMismatch(
            "Upper bounds ub must have length $n, got $(length(ub))"
        ))
    end
    
    if any(lb .> ub)
        invalid_pairs = findall(i -> lb[i] > ub[i], 1:n)
        throw(ArgumentError(
            "Lower bounds must be <= upper bounds. Invalid pairs: $invalid_pairs"
        ))
    end
end

"""
    validate_quadratic_matrix(Q, n)

Validate quadratic coefficient matrix.
"""
function validate_quadratic_matrix(Q::AbstractMatrix{<:Real}, n::Int)
    if size(Q) != (n, n)
        throw(DimensionMismatch(
            "Quadratic matrix Q must be $n×$n, got $(size(Q))"
        ))
    end
    
    if !isapprox(Q, Q', rtol=SYMMETRY_TOLERANCE)
        max_diff = maximum(abs.(Q - Q'))
        throw(ArgumentError(
            "Quadratic matrix Q must be symmetric. Max difference: $max_diff"
        ))
    end
end

"""
    validate_integer_variables(integer_vars, n)

Validate integer variable indices.
"""
function validate_integer_variables(integer_vars::AbstractVector{<:Integer}, n::Int)
    if !isempty(integer_vars)
        invalid_indices = filter(idx -> idx < 1 || idx > n, integer_vars)
        if !isempty(invalid_indices)
            throw(ArgumentError(
                "Integer variable indices must be in [1, $n], got invalid: $invalid_indices"
            ))
        end
        
        if length(unique(integer_vars)) != length(integer_vars)
            throw(ArgumentError("Integer variable indices must be unique"))
        end
    end
end

"""
    validate_quadratic_inputs(Q, c, A, b, lb, ub)

Validate inputs for quadratic programming problem.
"""
function validate_quadratic_inputs(
    Q::AbstractMatrix{<:Real},
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    lb::AbstractVector{<:Real},
    ub::AbstractVector{<:Real}
)
    n = length(c)
    
    if n == 0
        throw(ArgumentError("Coefficient vector c cannot be empty"))
    end
    
    validate_quadratic_matrix(Q, n)
    validate_linear_problem_dimensions(c, A, b, lb, ub)
    
    return n
end

"""
    validate_mip_inputs(c, A, b, integer_vars)

Validate inputs for mixed-integer programming problem.
"""
function validate_mip_inputs(
    c::AbstractVector{<:Real},
    A::AbstractMatrix{<:Real},
    b::AbstractVector{<:Real},
    integer_vars::AbstractVector{<:Integer}
)
    n = length(c)
    
    if n == 0
        throw(ArgumentError("Objective vector c cannot be empty"))
    end
    
    if size(A, 2) != n
        throw(DimensionMismatch(
            "Constraint matrix A must have $n columns, got $(size(A, 2))"
        ))
    end
    
    m = size(A, 1)
    if length(b) != m
        throw(DimensionMismatch(
            "Constraint vector b length $(length(b)) must match A rows $m"
        ))
    end
    
    validate_integer_variables(integer_vars, n)
    
    return n
end

