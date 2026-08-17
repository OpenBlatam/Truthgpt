"""
Transformer Configuration and Validation Types
"""

# Default configuration values
const DEFAULT_D_MODEL = 768
const DEFAULT_N_HEADS = 12
const DEFAULT_N_LAYERS = 12
const DEFAULT_D_FF = 3072
const DEFAULT_VOCAB_SIZE = 32000
const DEFAULT_MAX_SEQ_LEN = 2048
const DEFAULT_DROPOUT = 0.1f0
const DEFAULT_LAYER_NORM_EPS = 1f-5
const DEFAULT_ROPE_BASE = 10000.0f0

# Weight initialization
const DEFAULT_EMBED_SCALE = 0.02f0
const DEFAULT_LM_HEAD_SCALE = 0.02f0

# Generation defaults
const DEFAULT_MAX_NEW_TOKENS = 100
const DEFAULT_TEMPERATURE = 1.0f0
const DEFAULT_TOP_K = 50
const DEFAULT_TOP_P = 0.9f0
const DEFAULT_EOS_TOKEN_ID = 2

"""
    TransformerConfig

Transformer model configuration.
"""
Base.@kwdef struct TransformerConfig
    d_model::Int = DEFAULT_D_MODEL
    n_heads::Int = DEFAULT_N_HEADS
    n_layers::Int = DEFAULT_N_LAYERS
    d_ff::Int = DEFAULT_D_FF
    vocab_size::Int = DEFAULT_VOCAB_SIZE
    max_seq_len::Int = DEFAULT_MAX_SEQ_LEN
    dropout::Float32 = DEFAULT_DROPOUT
    layer_norm_eps::Float32 = DEFAULT_LAYER_NORM_EPS
    use_rope::Bool = true
    rope_base::Float32 = DEFAULT_ROPE_BASE
    
    function TransformerConfig(
        d_model::Int = DEFAULT_D_MODEL,
        n_heads::Int = DEFAULT_N_HEADS,
        n_layers::Int = DEFAULT_N_LAYERS,
        d_ff::Int = DEFAULT_D_FF,
        vocab_size::Int = DEFAULT_VOCAB_SIZE,
        max_seq_len::Int = DEFAULT_MAX_SEQ_LEN,
        dropout::Float32 = DEFAULT_DROPOUT,
        layer_norm_eps::Float32 = DEFAULT_LAYER_NORM_EPS,
        use_rope::Bool = true,
        rope_base::Float32 = DEFAULT_ROPE_BASE
    )
        validate_transformer_config(
            d_model, n_heads, n_layers, d_ff, vocab_size, max_seq_len, dropout
        )
        new(d_model, n_heads, n_layers, d_ff, vocab_size, max_seq_len,
            dropout, layer_norm_eps, use_rope, rope_base)
    end
end

function validate_transformer_config(
    d_model::Int,
    n_heads::Int,
    n_layers::Int,
    d_ff::Int,
    vocab_size::Int,
    max_seq_len::Int,
    dropout::Float32
)
    if d_model <= 0
        throw(ArgumentError("d_model must be positive, got $d_model"))
    end
    if n_heads <= 0
        throw(ArgumentError("n_heads must be positive, got $n_heads"))
    end
    if d_model % n_heads != 0
        throw(ArgumentError("d_model ($d_model) must be divisible by n_heads ($n_heads)"))
    end
    if n_layers <= 0
        throw(ArgumentError("n_layers must be positive, got $n_layers"))
    end
    if d_ff <= 0
        throw(ArgumentError("d_ff must be positive, got $d_ff"))
    end
    if vocab_size <= 0
        throw(ArgumentError("vocab_size must be positive, got $vocab_size"))
    end
    if max_seq_len <= 0
        throw(ArgumentError("max_seq_len must be positive, got $max_seq_len"))
    end
    if dropout < 0.0f0 || dropout > 1.0f0
        throw(ArgumentError("dropout must be in [0, 1], got $dropout"))
    end
end
