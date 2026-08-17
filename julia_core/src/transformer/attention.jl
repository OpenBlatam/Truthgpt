"""
Transformer Multi-Head Attention

MultiHeadAttention layer for the transformer architecture.
"""

"""
    MultiHeadAttention(config::TransformerConfig)

Create MultiHeadAttention layer from config.
"""
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

"""
    forward(attn, x; mask=nothing, start_pos=0)

Forward pass through multi-head attention.
"""
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
    
    scale_val = 1.0f0 / sqrt(Float32(attn.d_head))
    scores = zeros(Float32, batch, attn.n_heads, seq_len, seq_len)
    
    @inbounds for b in 1:batch, h in 1:attn.n_heads
        Q_head = @view Q[b, h, :, :]
        K_head = @view K[b, h, :, :]
        scores_head = Q_head * K_head'
        scores[b, h, :, :] = scores_head .* scale_val
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
    output = reshape(output, batch, seq_len, attn.d_model)
    
    return output
end
