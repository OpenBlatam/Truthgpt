"""
Transformer Feed-Forward Layer

FeedForward layer with SwiGLU activation.
"""

"""
    FeedForward(d_model, d_ff)

Create FeedForward layer.
"""
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

"""
    forward(ff, x)

Forward pass through feed-forward network using SwiGLU activation.
"""
function forward(ff::FeedForward, x::Array{Float32, 3})
    batch, seq_len, d_model = size(x)
    x_flat = reshape(x, :, d_model)
    
    gate = x_flat * ff.W_gate'
    up = x_flat * ff.W_up'
    
    hidden = swish(gate) .* up
    output = hidden * ff.W_down'
    
    return reshape(output, batch, seq_len, d_model)
end
