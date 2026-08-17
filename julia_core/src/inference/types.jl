"""
Inference & Sampling Types
"""

using Random

struct GenerationConfig
    max_new_tokens::Int
    temperature::Float32
    top_p::Float32
    top_k::Int
    repetition_penalty::Float32
    
    function GenerationConfig(;
        max_new_tokens::Int=100,
        temperature::Float32=0.8f0,
        top_p::Float32=0.9f0,
        top_k::Int=50,
        repetition_penalty::Float32=1.0f0
    )
        new(max_new_tokens, temperature, top_p, top_k, repetition_penalty)
    end
end

mutable struct TokenSampler
    rng::MersenneTwister
    TokenSampler(seed::Int=42) = new(MersenneTwister(seed))
end
