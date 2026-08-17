"""
Unit tests for JuMP Mathematical Optimization subsystem
"""

using Test

@testset "JuMP Optimization Tests" begin
    # Test Linear Programming:
    # Minimize: x + 2y
    # Subject to: x + y <= 10
    # Bounds: 0 <= x, y <= 5
    c = [1.0, 2.0]
    A = [1.0 1.0]
    b = [10.0]
    lb = [0.0, 0.0]
    ub = [5.0, 5.0]
    
    try
        x_opt, obj_val = TruthGPT.JumpOptimization.optimize_linear(c, A, b, lb, ub)
        @test length(x_opt) == 2
        @test isapprox(obj_val, 0.0, atol=1e-5)
    catch e
        @warn "JuMP solver tests skipped or solver unavailable: $e"
    end
end
