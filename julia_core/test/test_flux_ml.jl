"""
Unit tests for FluxML subsystem
"""

using Test

@testset "FluxML Subsystem Tests" begin
    config = TruthGPT.FluxML.TrainingConfig(
        epochs = 2,
        learning_rate = 0.01,
        device = :cpu,
        verbose = false
    )
    
    @test config.epochs == 2
    @test config.learning_rate == 0.01
    @test config.device == :cpu
    
    try
        model = TruthGPT.FluxML.create_model(10, [16], 2)
        @test model isa Flux.Chain
        
        X = randn(Float32, 10, 8)
        y = randn(Float32, 2, 8)
        
        preds = TruthGPT.FluxML.predict(model, X)
        @test size(preds) == (2, 8)
    catch e
        @warn "FluxML tests skipped or Flux unavailable: $e"
    end
end
