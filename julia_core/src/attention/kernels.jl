"""
Attention Kernels

Low-level computation helpers, numerical softmax, score calculation, and dropout.
"""

"""
    compute_qk_scores(Q, K, scale)

Compute Q @ K^T attention scores with scaling.
"""
function compute_qk_scores(Q::Array{T, 4}, K::Array{T, 4}, scale::T) where T
    batch, heads, seq_q, head_dim = size(Q)
    _, _, seq_k, _ = size(K)
    
    attn_scores = zeros(T, batch, heads, seq_q, seq_k)
    
    @inbounds for b in 1:batch, h in 1:heads, i in 1:seq_q, j in 1:seq_k
        sum_qk = zero(T)
        for d in 1:head_dim
            sum_qk += Q[b, h, i, d] * K[b, h, j, d]
        end
        attn_scores[b, h, i, j] = sum_qk * scale
    end
    
    return attn_scores
end

"""
    compute_attention_output(attn_weights, V)

Compute attention output from weights and values.
"""
function compute_attention_output(attn_weights::Array{T, 4}, V::Array{T, 4}) where T
    batch, heads, seq_q, seq_k = size(attn_weights)
    _, _, _, head_dim = size(V)
    
    output = zeros(T, batch, heads, seq_q, head_dim)
    
    @inbounds for b in 1:batch, h in 1:heads, i in 1:seq_q, d in 1:head_dim
        sum_v = zero(T)
        for j in 1:seq_k
            sum_v += attn_weights[b, h, i, j] * V[b, h, j, d]
        end
        output[b, h, i, d] = sum_v
    end
    
    return output
end

"""
    apply_causal_mask!(scores)

Apply causal mask in-place to attention scores.
"""
function apply_causal_mask!(scores::Array{T, 4}) where T
    _, _, seq_q, seq_k = size(scores)
    
    @inbounds for i in 1:seq_q, j in (i+1):seq_k
        scores[:, :, i, j] .= T(NEGATIVE_INFINITY)
    end
end

"""
    softmax_4d(x)

Compute softmax over the last dimension of a 4D tensor.
"""
function softmax_4d(x::Array{T, 4}) where T
    max_x = maximum(x, dims=4)
    exp_x = exp.(x .- max_x)
    return exp_x ./ sum(exp_x, dims=4)
end

"""
    apply_dropout(x, dropout_rate; rng=Random.GLOBAL_RNG, training=true)

Apply dropout to attention weights during training.
"""
function apply_dropout(
    x::Array{T, 4},
    dropout_rate::Float32;
    rng::AbstractRNG = Random.GLOBAL_RNG,
    training::Bool = true
) where T
    if dropout_rate <= 0.0f0 || !training
        return x
    end
    
    if dropout_rate >= 1.0f0
        return zeros(T, size(x))
    end
    
    mask = rand(rng, T, size(x)) .> dropout_rate
    scale_factor = T(1.0 / (1.0 - dropout_rate))
    
    return x .* mask .* scale_factor
end
