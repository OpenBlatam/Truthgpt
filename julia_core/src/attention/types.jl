"""
Attention Types

Type definitions and configurations for attention computation.
"""

"""
    AttentionConfig

Configuration for attention computation.

# Fields
- `num_heads`: Number of attention heads
- `head_dim`: Dimension of each attention head
- `dropout`: Dropout probability (0.0 = no dropout)
- `use_flash`: Use Flash Attention for memory efficiency
- `block_size`: Block size for Flash Attention
- `use_causal`: Use causal masking (for autoregressive models)

# Examples
```julia
config = AttentionConfig(
    num_heads=8,
    head_dim=64,
    use_flash=true,
    use_causal=true
)
```
"""
struct AttentionConfig
    num_heads::Int
    head_dim::Int
    dropout::Float32
    use_flash::Bool
    block_size::Int
    use_causal::Bool
    
    function AttentionConfig(
        num_heads::Int = DEFAULT_NUM_HEADS,
        head_dim::Int = DEFAULT_HEAD_DIM,
        dropout::Float32 = DEFAULT_DROPOUT,
        use_flash::Bool = true,
        block_size::Int = DEFAULT_BLOCK_SIZE,
        use_causal::Bool = true
    )
        validate_attention_config(num_heads, head_dim, dropout, block_size)
        new(num_heads, head_dim, dropout, use_flash, block_size, use_causal)
    end
end

"""
    AttentionConfig(; kwargs...)

Create AttentionConfig with keyword arguments.
"""
function AttentionConfig(;
    num_heads::Int = DEFAULT_NUM_HEADS,
    head_dim::Int = DEFAULT_HEAD_DIM,
    dropout::Float32 = DEFAULT_DROPOUT,
    use_flash::Bool = true,
    block_size::Int = DEFAULT_BLOCK_SIZE,
    use_causal::Bool = true
)
    AttentionConfig(num_heads, head_dim, dropout, use_flash, block_size, use_causal)
end

"""
    d_model(config::AttentionConfig)

Get total model dimension (num_heads * head_dim).
"""
d_model(config::AttentionConfig) = config.num_heads * config.head_dim

"""
    scale(config::AttentionConfig)

Get attention scale factor (1 / sqrt(head_dim)).
"""
scale(config::AttentionConfig) = Float32(1.0 / sqrt(config.head_dim))

"""
    MultiHeadAttention{T}

Multi-head attention layer with learnable projections.

# Fields
- `config`: AttentionConfig
- `Wq`: Query projection matrix [d_model, d_model]
- `Wk`: Key projection matrix [d_model, d_model]
- `Wv`: Value projection matrix [d_model, d_model]
- `Wo`: Output projection matrix [d_model, d_model]
"""
mutable struct MultiHeadAttention{T}
    config::AttentionConfig
    Wq::Matrix{T}
    Wk::Matrix{T}
    Wv::Matrix{T}
    Wo::Matrix{T}
end

"""
    RoPE{T}

Rotary Position Embeddings (RoPE) for relative position encoding.

# Fields
- `dim`: Dimension of embeddings
- `max_seq_len`: Maximum sequence length
- `cos_cache`: Cached cosine values [max_seq_len, half_dim]
- `sin_cache`: Cached sine values [max_seq_len, half_dim]
"""
struct RoPE{T}
    dim::Int
    max_seq_len::Int
    cos_cache::Matrix{T}
    sin_cache::Matrix{T}
end

"""
    AttentionOutput{T}

Output container for attention computation holding output tensor and optional attention weights.
"""
struct AttentionOutput{T}
    output::Array{T, 4}
    weights::Union{Array{T, 4}, Nothing}
end

