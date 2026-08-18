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

function sample_nucleus(
    sampler::TokenSampler,
    logits::Vector{T},
    config::GenerationConfig
) where T<:AbstractFloat
    scaled_logits = copy(logits)
    if config.temperature != 1.0f0 && config.temperature > 0.0f0
        scaled_logits ./= config.temperature
    end
    
    if config.top_k > 0
        return sample_topk(sampler, scaled_logits, config.top_k)
    elseif config.top_p < 1.0f0
        return sample_topp(sampler, scaled_logits, T(config.top_p))
    else
        probs = copy(scaled_logits)
        softmax!(probs)
        return wsample(sampler.rng, 1:length(probs), probs)
    end
end

function wsample(rng::AbstractRNG, items, weights)
    total_w = sum(weights)
    if total_w <= 0
        return items[rand(rng, 1:length(items))]
    end
    r = rand(rng) * total_w
    cumsum_val = zero(eltype(weights))
    for (item, w) in zip(items, weights)
        cumsum_val += w
        if cumsum_val >= r
            return item
        end
    end
    return items[end]
end

