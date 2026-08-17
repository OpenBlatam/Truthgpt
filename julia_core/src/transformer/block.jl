"""
Transformer Block

TransformerBlock layer with pre-norm architecture.
"""

"""
    TransformerBlock(config::TransformerConfig)

Create TransformerBlock from config.
"""
function TransformerBlock(config::TransformerConfig)
    return TransformerBlock(
        MultiHeadAttention(config),
        FeedForward(config.d_model, config.d_ff),
        ones(Float32, config.d_model),      # norm1_weight
        zeros(Float32, config.d_model),     # norm1_bias
        ones(Float32, config.d_model),      # norm2_weight
        zeros(Float32, config.d_model),     # norm2_bias
        config.layer_norm_eps
    )
end

"""
    forward(block, x; mask=nothing, start_pos=0)

Forward pass through transformer block using pre-norm residual connections.
"""
function forward(
    block::TransformerBlock,
    x::Array{Float32, 3};
    mask::Union{Nothing, Array{Float32}} = nothing,
    start_pos::Int = 0
)
    # Pre-norm + attention + residual
    normed = layer_norm(x, block.norm1_weight, block.norm1_bias, ε=block.eps)
    attn_out = forward(block.attention, normed, mask=mask, start_pos=start_pos)
    x = x .+ attn_out
    
    # Pre-norm + FFN + residual
    normed = layer_norm(x, block.norm2_weight, block.norm2_bias, ε=block.eps)
    ff_out = forward(block.ff, normed)
    x = x .+ ff_out
    
    return x
end
