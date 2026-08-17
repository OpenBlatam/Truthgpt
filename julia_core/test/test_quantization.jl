"""
Unit tests for Quantization subsystem
"""

using Test

@testset "Quantization Subsystem Tests" begin
    tensor = randn(Float32, 10, 10)
    
    @testset "INT8 Quantization" begin
        q_tensor = TruthGPT.Quantization.quantize_int8(tensor, symmetric=true)
        @test size(q_tensor.data) == (10, 10)
        @test eltype(q_tensor.data) == Int8
        
        deq = TruthGPT.Quantization.dequantize(q_tensor)
        @test size(deq) == (10, 10)
        @test eltype(deq) == Float32
        @test maximum(abs.(tensor .- deq)) < 0.1
    end
    
    @testset "INT4 Quantization" begin
        q_int4 = TruthGPT.Quantization.quantize_int4(tensor)
        deq_int4 = TruthGPT.Quantization.dequantize(q_int4)
        @test size(deq_int4) == (10, 10)
    end
end
