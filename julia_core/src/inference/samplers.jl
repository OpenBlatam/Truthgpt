"""
Sampling Algorithms for Token Generation (Greedy, Top-k, Top-p, Nucleus)
"""

using Random

function softmax!(probs::Vector{T}) where T<:AbstractFloat
    max_val = maximum(probs)
    probs .-= max_val
    probs .= exp.(probs)
    sum_val = sum(probs)
    if sum_val > zero(T)
        probs ./= sum_val
    end
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
    sum_top = sum(top_probs)
    if sum_top > zero(T)
        top_probs ./= sum_top
    end
    
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
    sum_top = sum(top_probs)
    if sum_top > zero(T)
        top_probs ./= sum_top
    end
    
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

function sample_nucleus(sampler::TokenSampler, logits::Vector{T}, p::T=T(0.9)) where T<:AbstractFloat
    return sample_topp(sampler, logits, p)
end
