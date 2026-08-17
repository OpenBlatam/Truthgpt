"""
Unit tests for Transformer subsystem
"""

using Test

@testset "Transformer Subsystem Tests" begin
    config = TruthGPT.Transformer.TransformerConfig(
        d_model = 32,
        n_heads = 4,
        n_layers = 2,
        d_ff = 64,
        vocab_size = 100,
        max_seq_len = 32
    )
    
    @test config.d_model == 32
    @test config.n_heads == 4
    
    model = TruthGPT.Transformer.Transformer(config)
    input_ids = fill(5, 2, 8)  # batch=2, seq_len=8
    
    logits = TruthGPT.Transformer.forward(model, input_ids)
    @test size(logits) == (2, 8, 100)
    
    generated = TruthGPT.Transformer.generate(model, [1, 2, 3], max_new_tokens=5)
    @test length(generated) <= 8
    @test length(generated) >= 3
end
