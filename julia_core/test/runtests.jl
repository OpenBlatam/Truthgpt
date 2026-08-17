"""
TruthGPT Julia Core Master Test Suite
"""

using Test
using LinearAlgebra
using Random

# Include module path
push!(LOAD_PATH, joinpath(@__DIR__, "..", "src"))

using TruthGPT

@testset "TruthGPT.jl Core Test Suite" begin
    @info "Running TruthGPT Test Suite..."
    
    include("test_utils.jl")
    include("test_attention.jl")
    include("test_cache.jl")
    include("test_quantization.jl")
    include("test_optimization.jl")
    include("test_jump.jl")
    include("test_flux_ml.jl")
    include("test_transformer.jl")
    include("test_compression.jl")
    include("test_inference.jl")
    
    @info "All TruthGPT tests completed successfully!"
end
