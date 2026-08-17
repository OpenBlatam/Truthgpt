"""
Attention Validation

Validation routines for attention configurations and input tensors.
"""

"""
    validate_attention_config(num_heads, head_dim, dropout, block_size)

Validate attention configuration parameters.
"""
function validate_attention_config(
    num_heads::Int,
    head_dim::Int,
    dropout::Float32,
    block_size::Int
)
    validate_num_heads(num_heads)
    validate_head_dim(head_dim)
    validate_attention_dropout(dropout)
    validate_block_size(block_size)
end

"""
    validate_num_heads(num_heads)

Validate number of attention heads.
"""
function validate_num_heads(num_heads::Int)
    if num_heads <= 0
        throw(ArgumentError("num_heads must be positive, got $num_heads"))
    end
end

"""
    validate_head_dim(head_dim)

Validate head dimension.
"""
function validate_head_dim(head_dim::Int)
    if head_dim <= 0
        throw(ArgumentError("head_dim must be positive, got $head_dim"))
    end
end

"""
    validate_attention_dropout(dropout)

Validate dropout probability for attention.
"""
function validate_attention_dropout(dropout::Float32)
    if dropout < 0.0f0 || dropout > 1.0f0
        throw(ArgumentError("dropout must be in [0, 1], got $dropout"))
    end
end

"""
    validate_block_size(block_size)

Validate block size for Flash Attention.
"""
function validate_block_size(block_size::Int)
    if block_size <= 0
        throw(ArgumentError("block_size must be positive, got $block_size"))
    end
end

"""
    validate_attention_inputs(Q, K, V)

Validate that Q, K, V tensors have compatible shapes.
"""
function validate_attention_inputs(Q, K, V)
    if ndims(Q) != 4 || ndims(K) != 4 || ndims(V) != 4
        throw(ArgumentError("Q, K, V must be 4D tensors [batch, heads, seq, head_dim]"))
    end
    
    batch_q, heads_q, seq_q, head_dim_q = size(Q)
    batch_k, heads_k, seq_k, head_dim_k = size(K)
    batch_v, heads_v, seq_v, head_dim_v = size(V)
    
    if batch_q != batch_k || batch_q != batch_v
        throw(DimensionMismatch("Batch sizes must match: Q=$batch_q, K=$batch_k, V=$batch_v"))
    end
    if heads_q != heads_k || heads_q != heads_v
        throw(DimensionMismatch("Head counts must match: Q=$heads_q, K=$heads_k, V=$heads_v"))
    end
    if head_dim_q != head_dim_k || head_dim_q != head_dim_v
        throw(DimensionMismatch("Head dimensions must match: Q=$head_dim_q, K=$head_dim_k, V=$head_dim_v"))
    end
    if seq_k != seq_v
        throw(DimensionMismatch("Key and value sequence lengths must match: K=$seq_k, V=$seq_v"))
    end
end
