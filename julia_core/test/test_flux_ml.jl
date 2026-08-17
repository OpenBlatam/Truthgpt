"""
Unit tests for FluxML subsystem
"""

using Test
using TruthGPT.FluxML

@testset "FluxML Subsystem Tests" begin
    @testset "Configuration and Defaults" begin
        config = TrainingConfig(
            learning_rate = 0.001f0,
            epochs = 5,
            batch_size = 32,
            optimizer = "adam",
            loss_function = "crossentropy",
            device = "cpu"
        )
        @test config.learning_rate == 0.001f0
        @test config.epochs == 5
        @test config.batch_size == 32
        @test config.device == "cpu"
    end
end
