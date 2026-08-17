"""
Scaled Dot-Product Attention Implementation
"""

using LinearAlgebra
using LoopVectorization
using Random

"""
    validate_attention_inputs(Q, K, V)
"""
function validate_attention_inputs(Q, K, V)
    if ndims(Q) != 4 || ndims(K) != 4 || ndims(V) != 4
        throw(ArgumentError("Q, K, V must be 4D tensors [batch, heads, seq, head_dim]"))
    end
    
    batch_q, heads_q, seq_q, head_dim_q = size(Q)
    batch_k, heads_k, seq_k, head_dim_k = size(K)
    batch_v, heads_v, seq_v, head_dim_v = size(V)
    
    if batch_q != batch_k || batch_q != batch_v
        throw(DimensionMismatch("Batch sizes must match: Q=$batch_q, K=$batch_k, V=$batch_v"))
    end
    if heads_q != heads_k || heads_q != heads_v
        throw(DimensionMismatch("Head counts must match: Q=$heads_q, K=$heads_k, V=$heads_v"))
    end
    if head_dim_q != head_dim_k || head_dim_q != head_dim_v
        throw(DimensionMismatch("Head dimensions must match: Q=$head_dim_q, K=$head_dim_k, V=$head_dim_v"))
    end
    if seq_k != seq_v
        throw(DimensionMismatch("Key and value sequence lengths must match: K=$seq_k, V=$seq_v"))
    end
end

"""
    compute_qk_scores(Q, K, scale)
"""
function compute_qk_scores(Q::Array{T, 4}, K::Array{T, 4}, scale::T) where T
    batch, heads, seq_q, head_dim = size(Q)
    _, _, seq_k, _ = size(K)
    
    attn_scores = zeros(T, batch, heads, seq_q, seq_k)
    
    @turbo for b in 1:batch, h in 1:heads, i in 1:seq_q, j in 1:seq_k
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
"""
function compute_attention_output(attn_weights::Array{T, 4}, V::Array{T, 4}) where T
    batch, heads, seq_q, seq_k = size(attn_weights)
    _, _, _, head_dim = size(V)
    
    output = zeros(T, batch, heads, seq_q, head_dim)
    
    @turbo for b in 1:batch, h in 1:heads, i in 1:seq_q, d in 1:head_dim
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
"""
function apply_causal_mask!(scores::Array{T, 4}) where T
    _, _, seq_q, seq_k = size(scores)
    
    @inbounds for i in 1:seq_q, j in (i+1):seq_k
        scores[:, :, i, j] .= T(NEGATIVE_INFINITY)
    end
end

"""
    softmax_4d(x)
"""
function softmax_4d(x::Array{T, 4}) where T
    max_x = maximum(x, dims=4)
    exp_x = exp.(x .- max_x)
    exp_x ./ sum(exp_x, dims=4)
end

"""
    apply_dropout(x, dropout_rate; rng=Random.GLOBAL_RNG, training=true)
"""
function apply_dropout(
    x::Array{T, 4},
    dropout_rate::Float32;
    rng::AbstractRNG=Random.GLOBAL_RNG,
    training::Bool=true
) where T
    if dropout_rate <= 0.0f0 || !training
        return x
    end
    if dropout_rate >= 1.0f0
        return zeros(T, size(x))
    end
    
    mask = rand(rng, T, size(x)) .> dropout_rate
    scale = T(1.0 / (1.0 - dropout_rate))
    return x .* mask .* scale
end

"""
    attention_forward(Q, K, V, config; mask=nothing)
"""
function attention_forward(
    Q::Array{T, 4},
    K::Array{T, 4},
    V::Array{T, 4},
    config::AttentionConfig;
    mask::Union{Nothing, AbstractArray} = nothing
) where T <: AbstractFloat
    validate_attention_inputs(Q, K, V)
    attn_scores = compute_qk_scores(Q, K, scale(config))
    
    if config.use_causal
        apply_causal_mask!(attn_scores)
    end
    
    if !isnothing(mask)
        if size(mask) != size(attn_scores)
            throw(DimensionMismatch("Mask size $(size(mask)) must match scores size $(size(attn_scores))"))
        end
        attn_scores .+= mask
    end
    
    attn_weights = softmax_4d(attn_scores)
    
    if config.dropout > 0.0f0
        attn_weights = apply_dropout(attn_weights, config.dropout, training=true)
    end
    
    return compute_attention_output(attn_weights, V)
end
