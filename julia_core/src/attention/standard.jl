"""
Standard Attention

Standard scaled dot-product attention forward pass.
"""

"""
    attention_forward(Q, K, V, config; mask=nothing)

Compute scaled dot-product attention.

# Arguments
- `Q`: Query tensor [batch, heads, seq_q, head_dim]
- `K`: Key tensor [batch, heads, seq_k, head_dim]
- `V`: Value tensor [batch, heads, seq_k, head_dim]
- `config`: AttentionConfig
- `mask`: Optional attention mask (added to scores before softmax)

# Returns
- Output tensor [batch, heads, seq_q, head_dim]
"""
function attention_forward(
    Q::Array{T, 4},
    K::Array{T, 4},
    V::Array{T, 4},
    config::AttentionConfig;
    mask::Union{Nothing, AbstractArray} = nothing
) where T <: AbstractFloat
    # Validate inputs
    validate_attention_inputs(Q, K, V)
    
    # Compute attention scores: Q @ K^T / sqrt(head_dim)
    attn_scores = compute_qk_scores(Q, K, scale(config))
    
    # Apply causal mask if needed
    if config.use_causal
        apply_causal_mask!(attn_scores)
    end
    
    # Apply optional mask
    if !isnothing(mask)
        if size(mask) != size(attn_scores)
            throw(DimensionMismatch("Mask size $(size(mask)) must match scores size $(size(attn_scores))"))
        end
        attn_scores .+= mask
    end
    
    # Compute attention weights with softmax
    attn_weights = softmax_4d(attn_scores)
    
    # Apply dropout if specified (only during training)
    if config.dropout > 0.0f0
        attn_weights = apply_dropout(attn_weights, config.dropout, training=true)
    end
    
    # Compute output: attn_weights @ V
    output = compute_attention_output(attn_weights, V)
    
    return output
end
