"""
Token Generation with Top-k and Top-p (Nucleus) Sampling
"""

"""
    generate(model, input_ids; max_new_tokens=100, temperature=1.0, top_k=50, top_p=0.9)

Generate tokens using the transformer model.
"""
function generate(
    model::Transformer,
    input_ids::Vector{Int};
    max_new_tokens::Int = DEFAULT_MAX_NEW_TOKENS,
    temperature::Float32 = DEFAULT_TEMPERATURE,
    top_k::Int = DEFAULT_TOP_K,
    top_p::Float32 = DEFAULT_TOP_P
)
    if isempty(input_ids)
        throw(ArgumentError("input_ids cannot be empty"))
    end
    if max_new_tokens <= 0
        throw(ArgumentError("max_new_tokens must be positive, got $max_new_tokens"))
    end
    if temperature <= 0.0f0
        throw(ArgumentError("temperature must be positive, got $temperature"))
    end
    if top_k <= 0
        throw(ArgumentError("top_k must be positive, got $top_k"))
    end
    if top_p <= 0.0f0 || top_p > 1.0f0
        throw(ArgumentError("top_p must be in (0, 1], got $top_p"))
    end
    
    tokens = copy(input_ids)
    
    for _ in 1:max_new_tokens
        input_batch = reshape(tokens, 1, :)
        logits = forward(model, input_batch)
        next_token_logits = logits[1, end, :]
        
        if temperature != 1.0f0
            next_token_logits ./= temperature
        end
        
        probs = softmax(next_token_logits)
        next_token = sample_top_k_top_p(probs, top_k, top_p)
        
        push!(tokens, next_token)
        
        if next_token == DEFAULT_EOS_TOKEN_ID
            break
        end
    end
    
    return tokens
end

"""
    sample_top_k_top_p(probs, top_k, top_p)

Sample from distribution with top-k and top-p filtering.
"""
function sample_top_k_top_p(probs::Vector{Float32}, top_k::Int, top_p::Float32)
    if isempty(probs)
        throw(ArgumentError("probs cannot be empty"))
    end
    if top_k <= 0
        throw(ArgumentError("top_k must be positive, got $top_k"))
    end
    if top_p <= 0.0f0 || top_p > 1.0f0
        throw(ArgumentError("top_p must be in (0, 1], got $top_p"))
    end
    
    sorted_indices = sortperm(probs, rev=true)
    k_limit = min(top_k, length(probs))
    top_k_indices = sorted_indices[1:k_limit]
    
    cumsum_probs = 0.0f0
    cutoff_idx = length(top_k_indices)
    
    @inbounds for (i, idx) in enumerate(top_k_indices)
        cumsum_probs += probs[idx]
        if cumsum_probs >= top_p
            cutoff_idx = i
            break
        end
    end
    
    filtered_indices = top_k_indices[1:cutoff_idx]
    filtered_probs = probs[filtered_indices]
    
    prob_sum = sum(filtered_probs)
    if prob_sum > 0.0f0
        filtered_probs ./= prob_sum
    else
        filtered_probs = fill(1.0f0 / length(filtered_indices), length(filtered_indices))
    end
    
    r = rand(Float32)
    cumsum = 0.0f0
    
    @inbounds for (prob, idx) in zip(filtered_probs, filtered_indices)
        cumsum += prob
        if r <= cumsum
            return idx - 1  # 0-indexed return
        end
    end
    
    return filtered_indices[end] - 1
end
