"""
Unit tests for Optimization subsystem
"""

using Test

@testset "Optimization Subsystem Tests" begin
    bounds = TruthGPT.Optimization.HyperparamBounds(
        lr_range = (1e-5, 1e-2),
        batch_range = (16, 64)
    )
    
    @test bounds.lr_min == 1e-5
    @test bounds.lr_max == 1e-2
    @test bounds.batch_min == 16
    @test bounds.batch_max == 64
    
    # Loss function for testing
    dummy_loss(params) = (log(params[:lr]) - log(1e-3))^2 + (params[:batch_size] - 32)^2
    
    res = TruthGPT.Optimization.optimize_hyperparams(
        dummy_loss,
        bounds,
        method = :random,
        max_iters = 10
    )
    
    @test res isa TruthGPT.Optimization.OptimizationResult
    @test res.iterations == 10
    @test length(res.history) == 10
    @test res.best_loss < Inf
    @test haskey(res.best_params, :lr)
    @test haskey(res.best_params, :batch_size)
    
    # Schedulers
    lr_c = TruthGPT.Optimization.cosine_schedule(500, 1000, 0.01)
    @test lr_c > 0.0 && lr_c < 0.01
    
    lr_w = TruthGPT.Optimization.linear_warmup(50, 100, 0.01)
    @test isapprox(lr_w, 0.005, atol=1e-5)
end
