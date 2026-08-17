"""
Transformer Validation

Validation helpers for transformer configurations and RoPE dimensions.
"""

"""
    validate_transformer_config(d_model, n_heads, n_layers, d_ff, vocab_size, max_seq_len, dropout)

Validate transformer configuration parameters.
"""
function validate_transformer_config(
    d_model::Int,
    n_heads::Int,
    n_layers::Int,
    d_ff::Int,
    vocab_size::Int,
    max_seq_len::Int,
    dropout::Float32
)
    validate_d_model(d_model)
    validate_n_heads(n_heads)
    validate_head_divisibility(d_model, n_heads)
    validate_n_layers(n_layers)
    validate_d_ff(d_ff)
    validate_vocab_size(vocab_size)
    validate_max_seq_len(max_seq_len)
    validate_dropout(dropout)
end

"""
    validate_d_model(d_model)

Validate model dimension.
"""
function validate_d_model(d_model::Int)
    if d_model <= 0
        throw(ArgumentError("d_model must be positive, got $d_model"))
    end
end

"""
    validate_n_heads(n_heads)

Validate number of attention heads.
"""
function validate_n_heads(n_heads::Int)
    if n_heads <= 0
        throw(ArgumentError("n_heads must be positive, got $n_heads"))
    end
end

"""
    validate_head_divisibility(d_model, n_heads)

Validate that d_model is divisible by n_heads.
"""
function validate_head_divisibility(d_model::Int, n_heads::Int)
    if d_model % n_heads != 0
        throw(ArgumentError("d_model ($d_model) must be divisible by n_heads ($n_heads)"))
    end
end

"""
    validate_n_layers(n_layers)

Validate number of transformer layers.
"""
function validate_n_layers(n_layers::Int)
    if n_layers <= 0
        throw(ArgumentError("n_layers must be positive, got $n_layers"))
    end
end

"""
    validate_d_ff(d_ff)

Validate feed-forward dimension.
"""
function validate_d_ff(d_ff::Int)
    if d_ff <= 0
        throw(ArgumentError("d_ff must be positive, got $d_ff"))
    end
end

"""
    validate_vocab_size(vocab_size)

Validate vocabulary size.
"""
function validate_vocab_size(vocab_size::Int)
    if vocab_size <= 0
        throw(ArgumentError("vocab_size must be positive, got $vocab_size"))
    end
end

"""
    validate_max_seq_len(max_seq_len)

Validate maximum sequence length.
"""
function validate_max_seq_len(max_seq_len::Int)
    if max_seq_len <= 0
        throw(ArgumentError("max_seq_len must be positive, got $max_seq_len"))
    end
end

"""
    validate_dropout(dropout)

Validate dropout probability.
"""
function validate_dropout(dropout::Float32)
    if dropout < 0.0f0 || dropout > 1.0f0
        throw(ArgumentError("dropout must be in [0, 1], got $dropout"))
    end
end

"""
    validate_rope_dim(dim)

Validate dimension for RoPE (must be positive and even).
"""
function validate_rope_dim(dim::Int)
    if dim <= 0 || dim % 2 != 0
        throw(ArgumentError("dim must be positive and even, got $dim"))
    end
end
