"""
Transformer Layers: MultiHeadAttention, FeedForward (SwiGLU), TransformerBlock
"""

using LinearAlgebra

"""
    MultiHeadAttention

Multi-head attention layer with RoPE support.
"""
mutable struct MultiHeadAttention
    d_model::Int
    n_heads::Int
    d_head::Int
    
    W_q::Matrix{Float32}
    W_k::Matrix{Float32}
    W_v::Matrix{Float32}
    W_o::Matrix{Float32}
    
    cos_cache::Matrix{Float32}
    sin_cache::Matrix{Float32}
    use_rope::Bool
end

function MultiHeadAttention(config::TransformerConfig)
    d_head = config.d_model ÷ config.n_heads
    
    W_q = xavier_init(config.d_model, config.d_model)
    W_k = xavier_init(config.d_model, config.d_model)
    W_v = xavier_init(config.d_model, config.d_model)
    W_o = xavier_init(config.d_model, config.d_model)
    
    if config.use_rope
        cos_cache, sin_cache = precompute_rope_freqs(
            d_head, config.max_seq_len, base=config.rope_base
        )
    else
        cos_cache = zeros(Float32, 1, 1)
        sin_cache = zeros(Float32, 1, 1)
    end
    
    return MultiHeadAttention(
        config.d_model, config.n_heads, d_head,
        W_q, W_k, W_v, W_o,
        cos_cache, sin_cache, config.use_rope
    )
end

function forward(
    attn::MultiHeadAttention,
    x::Array{Float32, 3};
    mask::Union{Nothing, Array{Float32}} = nothing,
    start_pos::Int = 0
)
    batch, seq_len, d_model = size(x)
    
    if d_model != attn.d_model
        throw(DimensionMismatch(
            "Input dimension $d_model must match d_model $(attn.d_model)"
        ))
    end
    
    x_flat = reshape(x, :, d_model)
    Q = x_flat * attn.W_q'
    K = x_flat * attn.W_k'
    V = x_flat * attn.W_v'
    
    Q = reshape(Q, batch, seq_len, attn.n_heads, attn.d_head)
    K = reshape(K, batch, seq_len, attn.n_heads, attn.d_head)
    V = reshape(V, batch, seq_len, attn.n_heads, attn.d_head)
    
    Q = permutedims(Q, (1, 3, 2, 4))
    K = permutedims(K, (1, 3, 2, 4))
    V = permutedims(V, (1, 3, 2, 4))
    
    if attn.use_rope
        @inbounds for h in 1:attn.n_heads
            q_head = @view Q[:, h, :, :]
            k_head = @view K[:, h, :, :]
            
            q_rotated, k_rotated = apply_rope(
                q_head, k_head, attn.cos_cache, attn.sin_cache, start_pos=start_pos
            )
            
            Q[:, h, :, :] = q_rotated
            K[:, h, :, :] = k_rotated
        end
    end
    
    scale = 1.0f0 / sqrt(Float32(attn.d_head))
    scores = zeros(Float32, batch, attn.n_heads, seq_len, seq_len)
    
    @inbounds for b in 1:batch, h in 1:attn.n_heads
        Q_head = @view Q[b, h, :, :]
        K_head = @view K[b, h, :, :]
        scores_head = Q_head * K_head'
        scores[b, h, :, :] = scores_head .* scale
    end
    
    if !isnothing(mask)
        if size(mask) != size(scores)
            throw(DimensionMismatch(
                "Mask size $(size(mask)) must match scores size $(size(scores))"
            ))
        end
        scores = scores .+ mask
    end
    
    attn_weights = softmax(scores, dims=4)
    output = zeros(Float32, batch, attn.n_heads, seq_len, attn.d_head)
    
    @inbounds for b in 1:batch, h in 1:attn.n_heads
        attn_weights_head = @view attn_weights[b, h, :, :]
        V_head = @view V[b, h, :, :]
        output[b, h, :, :] = attn_weights_head * V_head
    end
    
    output = permutedims(output, (1, 3, 2, 4))
    output = reshape(output, batch, seq_len, attn.d_model)
    
    output_flat = reshape(output, :, attn.d_model)
    output = output_flat * attn.W_o'
    return reshape(output, batch, seq_len, attn.d_model)
end

"""
    FeedForward

Feed-forward network with SwiGLU activation.
"""
mutable struct FeedForward
    W_gate::Matrix{Float32}
    W_up::Matrix{Float32}
    W_down::Matrix{Float32}
end

function FeedForward(d_model::Int, d_ff::Int)
    if d_model <= 0
        throw(ArgumentError("d_model must be positive, got $d_model"))
    end
    if d_ff <= 0
        throw(ArgumentError("d_ff must be positive, got $d_ff"))
    end
    
    return FeedForward(
        xavier_init(d_model, d_ff),
        xavier_init(d_model, d_ff),
        xavier_init(d_ff, d_model)
    )
end

function forward(ff::FeedForward, x::Array{Float32, 3})
    batch, seq_len, d_model = size(x)
    x_flat = reshape(x, :, d_model)
    
    gate = x_flat * ff.W_gate'
    up = x_flat * ff.W_up'
    hidden = swish(gate) .* up
    
    output = hidden * ff.W_down'
    return reshape(output, batch, seq_len, d_model)
end

"""
    TransformerBlock

Single transformer block with pre-norm architecture.
"""
mutable struct TransformerBlock
    attention::MultiHeadAttention
    ff::FeedForward
    norm1_weight::Vector{Float32}
    norm1_bias::Vector{Float32}
    norm2_weight::Vector{Float32}
    norm2_bias::Vector{Float32}
    eps::Float32
end

function TransformerBlock(config::TransformerConfig)
    return TransformerBlock(
        MultiHeadAttention(config),
        FeedForward(config.d_model, config.d_ff),
        ones(Float32, config.d_model),
        zeros(Float32, config.d_model),
        ones(Float32, config.d_model),
        zeros(Float32, config.d_model),
        config.layer_norm_eps
    )
end

function forward(
    block::TransformerBlock,
    x::Array{Float32, 3};
    mask::Union{Nothing, Array{Float32}} = nothing,
    start_pos::Int = 0
)
    normed = layer_norm(x, block.norm1_weight, block.norm1_bias, ε=block.eps)
    attn_out = forward(block.attention, normed, mask=mask, start_pos=start_pos)
    x = x .+ attn_out
    
    normed = layer_norm(x, block.norm2_weight, block.norm2_bias, ε=block.eps)
    ff_out = forward(block.ff, normed)
    x = x .+ ff_out
    
    return x
end

"""
    create_causal_mask(seq_len, start_pos=0)

Create causal attention mask.
"""
function create_causal_mask(seq_len::Int, start_pos::Int = 0)
    if seq_len <= 0
        throw(ArgumentError("seq_len must be positive, got $seq_len"))
    end
    
    mask = fill(-Inf32, seq_len, seq_len)
    @inbounds for i in 1:seq_len
        for j in 1:i
            mask[i, j] = 0.0f0
        end
    end
    return reshape(mask, 1, 1, seq_len, seq_len)
end
