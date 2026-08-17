"""
TruthGPT Inference Submodule

Sampling and generation configuration routines.
"""
module Inference

using Random

export TokenSampler, sample_greedy, sample_topk, sample_topp, sample_nucleus
export GenerationConfig

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

function softmax!(probs::Vector{T}) where T<:AbstractFloat
    max_val = maximum(probs)
    probs .-= max_val
    probs .= exp.(probs)
    probs ./= sum(probs)
    return probs
end

function sample_greedy(logits::Vector{T}) where T<:AbstractFloat
    return argmax(logits)
end

function sample_topk(sampler::TokenSampler, logits::Vector{T}, k::Int) where T<:AbstractFloat
    probs = copy(logits)
    softmax!(probs)
    
    indices = partialsortperm(probs, 1:min(k, length(probs)), rev=true)
    top_probs = probs[indices]
    top_probs ./= sum(top_probs)
    
    r = rand(sampler.rng)
    cumsum_val = 0.0
    for (i, p) in enumerate(top_probs)
        cumsum_val += p
        if cumsum_val >= r
            return indices[i]
        end
    end
    
    return indices[end]
end

function sample_topp(sampler::TokenSampler, logits::Vector{T}, p::T) where T<:AbstractFloat
    probs = copy(logits)
    softmax!(probs)
    
    sorted_indices = sortperm(probs, rev=true)
    sorted_probs = probs[sorted_indices]
    cumsum_probs = cumsum(sorted_probs)
    
    cutoff_idx = findfirst(x -> x >= p, cumsum_probs)
    cutoff_idx = isnothing(cutoff_idx) ? length(probs) : cutoff_idx
    
    top_indices = sorted_indices[1:cutoff_idx]
    top_probs = sorted_probs[1:cutoff_idx]
    top_probs ./= sum(top_probs)
    
    r = rand(sampler.rng)
    cumsum_val = 0.0
    for (i, prob) in enumerate(top_probs)
        cumsum_val += prob
        if cumsum_val >= r
            return top_indices[i]
        end
    end
    
    return top_indices[end]
end

function sample_nucleus(
    sampler::TokenSampler,
    logits::Vector{T},
    config::GenerationConfig
) where T<:AbstractFloat
    if config.temperature != 1.0f0
        logits = logits ./ config.temperature
    end
    
    if config.top_k > 0
        token = sample_topk(sampler, logits, config.top_k)
    elseif config.top_p < 1.0f0
        token = sample_topp(sampler, logits, config.top_p)
    else
        probs = copy(logits)
        softmax!(probs)
        token = wsample(sampler.rng, 1:length(probs), probs)
    end
    
    return token
end

function wsample(rng::MersenneTwister, items, weights)
    r = rand(rng) * sum(weights)
    cumsum_val = 0.0
    for (item, w) in zip(items, weights)
        cumsum_val += w
        if cumsum_val >= r
            return item
        end
    end
    return items[end]
end

end # module Inference
