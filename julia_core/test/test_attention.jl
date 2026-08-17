"""
Unit tests for Attention subsystem
"""

using Test

@testset "Attention Subsystem Tests" begin
    config = TruthGPT.Attention.AttentionConfig(
        num_heads = 4,
        head_dim = 16,
        dropout = 0.0f0,
        use_flash = true,
        block_size = 16,
        use_causal = true
    )
    
    @test TruthGPT.Attention.d_model(config) == 64
    @test isapprox(TruthGPT.Attention.scale(config), 0.25f0, atol=1e-5)
    
    batch, heads, seq_len, head_dim = 2, 4, 16, 16
    Q = randn(Float32, batch, heads, seq_len, head_dim)
    K = randn(Float32, batch, heads, seq_len, head_dim)
    V = randn(Float32, batch, heads, seq_len, head_dim)
    
    @testset "Flash Attention" begin
        out = TruthGPT.Attention.flash_attention(Q, K, V, config)
        @test size(out) == (batch, heads, seq_len, head_dim)
    end
    
    @testset "Standard Attention" begin
        out = TruthGPT.Attention.attention_forward(Q, K, V, config)
        @test size(out) == (batch, heads, seq_len, head_dim)
    end
    
    @testset "RoPE" begin
        rope = TruthGPT.Attention.RoPE(head_dim, seq_len)
        Q_rot = copy(Q)
        K_rot = copy(K)
        TruthGPT.Attention.apply_rope!(Q_rot, K_rot, rope)
        @test size(Q_rot) == size(Q)
        @test size(K_rot) == size(K)
    end
end
