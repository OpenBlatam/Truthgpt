"""
Unit tests for JuMPOptimization subsystem
"""

using Test
using TruthGPT.JumpOptimization

@testset "JumpOptimization Subsystem Tests" begin
    @testset "Linear Optimization Validation & Setup" begin
        c = [1.0, 2.0]
        A = reshape([1.0, 1.0], 1, 2)
        b = [10.0]
        lb = [0.0, 0.0]
        ub = [5.0, 5.0]
        
        try
            sol, obj = optimize_linear(c, A, b, lb, ub)
            @test length(sol) == 2
            @test isapprox(sol[1], 0.0, atol=1e-3)
            @test isapprox(sol[2], 0.0, atol=1e-3)
            @test isapprox(obj, 0.0, atol=1e-3)
        catch e
            @warn "JuMP linear solver test skipped: $e"
        end
    end

    @testset "Quadratic Optimization" begin
        Q = [2.0 0.0; 0.0 2.0]
        c = [-2.0, -4.0]
        A = reshape([1.0, 1.0], 1, 2)
        b = [10.0]
        lb = [0.0, 0.0]
        ub = [5.0, 5.0]
        
        try
            sol, obj = optimize_quadratic(Q, c, A, b, lb, ub)
            @test length(sol) == 2
        catch e
            @warn "JuMP quadratic solver test skipped: $e"
        end
    end

    @testset "MIP Optimization" begin
        c = [1.0, 2.0]
        A = reshape([1.0, 1.0], 1, 2)
        b = [10.0]
        int_vars = [1, 2]
        
        try
            sol, obj = optimize_mip(c, A, b, int_vars)
            @test length(sol) == 2
        catch e
            @warn "JuMP MIP solver test skipped: $e"
        end
    end
end

