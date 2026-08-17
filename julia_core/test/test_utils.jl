"""
Unit tests for Utils subsystem
"""

using Test

@testset "Utils Subsystem Tests" begin
    @testset "Data Conversion" begin
        x = randn(Float64, 4, 4)
        x_f32 = TruthGPT.Utils.to_float32(x)
        @test eltype(x_f32) == Float32
        @test size(x_f32) == (4, 4)
        
        x_f16 = TruthGPT.Utils.to_float16(x)
        @test eltype(x_f16) == Float16
        
        x_bf16 = TruthGPT.Utils.to_bfloat16(x_f32)
        @test eltype(x_bf16) == UInt16
        
        x_restored = TruthGPT.Utils.from_bfloat16(x_bf16)
        @test eltype(x_restored) == Float32
        @test isapprox(x_f32, x_restored, rtol=1e-2)
    end
    
    @testset "Activations & Normalization" begin
        x = Float32[-2.0, -1.0, 0.0, 1.0, 2.0]
        
        sig = TruthGPT.Utils.sigmoid(x)
        @test all(sig .>= 0.0f0) && all(sig .<= 1.0f0)
        @test isapprox(sig[3], 0.5f0, atol=1e-5)
        
        sw = TruthGPT.Utils.swish(x)
        @test isapprox(sw[3], 0.0f0, atol=1e-5)
        
        g = TruthGPT.Utils.gelu(x)
        @test isapprox(g[3], 0.0f0, atol=1e-5)
        
        sm = TruthGPT.Utils.softmax(x)
        @test isapprox(sum(sm), 1.0f0, atol=1e-5)
        
        mat = randn(Float32, 5, 10)
        γ = ones(Float32, 1, 10)
        β = zeros(Float32, 1, 10)
        ln = TruthGPT.Utils.layer_norm(mat, γ, β)
        @test size(ln) == (5, 10)
    end
    
    @testset "Formatting Helpers" begin
        @test TruthGPT.Utils.format_bytes(1024) == "1.0 KB"
        @test TruthGPT.Utils.format_bytes(1024^2) == "1.0 MB"
        @test TruthGPT.Utils.format_time(500) == "500.0ns"
    end
end
