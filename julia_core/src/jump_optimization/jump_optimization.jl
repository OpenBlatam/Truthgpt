"""
JuMP.jl Optimization Module

High-performance mathematical optimization using JuMP.jl with support for:
- Linear programming (LP)
- Quadratic programming (QP)
- Mixed-integer programming (MIP)
- Multiple solver backends (HiGHS, Gurobi, CPLEX, etc.)
"""

using JuMP
using HiGHS

include("constants.jl")
include("validation.jl")
include("helpers.jl")
include("linear.jl")
include("quadratic.jl")
include("mip.jl")
include("hyperparams.jl")

export optimize_linear, optimize_quadratic, optimize_mip
export optimize_hyperparameters
export DEFAULT_SOLVER, STATUS_OPTIMAL

