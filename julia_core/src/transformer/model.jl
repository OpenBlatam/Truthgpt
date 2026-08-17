"""
Full Transformer Architecture and Forward Pass
"""

using LinearAlgebra

"""
    Transformer

Full transformer model.
"""
mutable struct Transformer
    config::TransformerConfig
    embed::Matrix{Float32}
    blocks::Vector{TransformerBlock}
    final_norm_weight::Vector{Float32}
    final_norm_bias::Vector{Float32}
    lm_head::Matrix{Float32}
end

function Transformer(config::TransformerConfig)
    embed = randn(Float32, config.vocab_size, config.d_model) .* DEFAULT_EMBED_SCALE
    blocks = [TransformerBlock(config) for _ in 1:config.n_layers]
    final_norm_weight = ones(Float32, config.d_model)
    final_norm_bias = zeros(Float32, config.d_model)
    lm_head = randn(Float32, config.d_model, config.vocab_size) .* DEFAULT_LM_HEAD_SCALE
    
    return Transformer(
        config, embed, blocks, final_norm_weight, final_norm_bias, lm_head
    )
end

function forward(
    model::Transformer,
    input_ids::Array{Int, 2};
    start_pos::Int = 0
)
    batch, seq_len = size(input_ids)
    
    if any(id -> id < 0 || id >= model.config.vocab_size, input_ids)
        throw(ArgumentError(
            "Input IDs must be in [0, vocab_size-1] = [0, $(model.config.vocab_size-1)]"
        ))
    end
    
    x = model.embed[input_ids .+ 1, :]
    x = reshape(x, batch, seq_len, model.config.d_model)
    
    mask = create_causal_mask(seq_len, start_pos)
    
    for block in model.blocks
        x = forward(block, x, mask=mask, start_pos=start_pos)
    end
    
    x = layer_norm(
        x, model.final_norm_weight, model.final_norm_bias,
        ε=model.config.layer_norm_eps
    )
    
    x_flat = reshape(x, :, model.config.d_model)
    logits = x_flat * model.lm_head
    logits = reshape(logits, batch, seq_len, model.config.vocab_size)
    
    return logits
end
