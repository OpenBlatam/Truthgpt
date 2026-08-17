"""
Multi-Head Attention Layer

MultiHeadAttention layer constructor and forward execution.
"""

"""
    MultiHeadAttention(config; T::Type=Float32)

Create a MultiHeadAttention layer with Xavier initialization.
"""
function MultiHeadAttention(config::AttentionConfig; T::Type = Float32)
    d = d_model(config)
    scale_factor = T(sqrt(DEFAULT_XAVIER_SCALE / d))
    
    Wq = randn(T, d, d) * scale_factor
    Wk = randn(T, d, d) * scale_factor
    Wv = randn(T, d, d) * scale_factor
    Wo = randn(T, d, d) * scale_factor
    
    return MultiHeadAttention(config, Wq, Wk, Wv, Wo)
end

"""
    forward(mha, x; kv_cache=nothing)

Forward pass through multi-head attention.

# Arguments
- `mha`: MultiHeadAttention layer
- `x`: Input tensor [batch, seq_len, d_model]
- `kv_cache`: Optional KV cache
"""
function forward(mha::MultiHeadAttention, x::Array{T, 3}; kv_cache = nothing) where T
    batch, seq_len, d = size(x)
    config = mha.config
    
    if d != d_model(config)
        throw(DimensionMismatch(
            "Input dimension $d must match d_model $(d_model(config))"
        ))
    end
    
    x_flat = reshape(x, batch * seq_len, d)
    
    Q = x_flat * mha.Wq
    K = x_flat * mha.Wk
    V = x_flat * mha.Wv
    
    Q = reshape(Q, batch, seq_len, config.num_heads, config.head_dim)
    K = reshape(K, batch, seq_len, config.num_heads, config.head_dim)
    V = reshape(V, batch, seq_len, config.num_heads, config.head_dim)
    
    Q = permutedims(Q, (1, 3, 2, 4))
    K = permutedims(K, (1, 3, 2, 4))
    V = permutedims(V, (1, 3, 2, 4))
    
    if config.use_flash
        attn_out = flash_attention(Q, K, V, config)
    else
        attn_out = attention_forward(Q, K, V, config)
    end
    
    attn_out = permutedims(attn_out, (1, 3, 2, 4))
    attn_out = reshape(attn_out, batch * seq_len, d)
    output = attn_out * mha.Wo
    
    return reshape(output, batch, seq_len, d)
end
