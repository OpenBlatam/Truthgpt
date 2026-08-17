"""
Rotary Position Embeddings (RoPE)

RoPE constructor and rotary embedding application.
"""

"""
    RoPE(dim, max_seq_len; T::Type=Float32, base=10000.0)

Create RoPE with precomputed rotation matrices.
"""
function RoPE(
    dim::Int,
    max_seq_len::Int;
    T::Type = Float32,
    base::T = T(DEFAULT_ROPE_BASE)
)
    if dim <= 0 || dim % 2 != 0
        throw(ArgumentError("dim must be positive and even, got $dim"))
    end
    if max_seq_len <= 0
        throw(ArgumentError("max_seq_len must be positive, got $max_seq_len"))
    end
    
    half_dim = dim ÷ 2
    inv_freq = T[1.0 / (base^(2i / dim)) for i in 0:(half_dim-1)]
    
    cos_cache = zeros(T, max_seq_len, half_dim)
    sin_cache = zeros(T, max_seq_len, half_dim)
    
    for pos in 1:max_seq_len
        for (i, freq) in enumerate(inv_freq)
            angle = (pos - 1) * freq
            cos_cache[pos, i] = cos(angle)
            sin_cache[pos, i] = sin(angle)
        end
    end
    
    return RoPE(dim, max_seq_len, cos_cache, sin_cache)
end

"""
    apply_rope!(q, k, rope, start_pos=1)

Apply rotary position embeddings in-place to Q and K tensors.
"""
function apply_rope!(
    q::Array{T, 4},
    k::Array{T, 4},
    rope::RoPE,
    start_pos::Int = 1
) where T
    batch, heads, seq_len, head_dim = size(q)
    
    if head_dim != rope.dim
        throw(DimensionMismatch(
            "head_dim $head_dim must match rope.dim $(rope.dim)"
        ))
    end
    if size(k) != size(q)
        throw(DimensionMismatch("Q and K must have same shape"))
    end
    
    half_dim = head_dim ÷ 2
    
    @inbounds for b in 1:batch, h in 1:heads, s in 1:seq_len
        pos = start_pos + s - 1
        
        if pos > rope.max_seq_len
            throw(ArgumentError(
                "Position $pos exceeds max_seq_len $(rope.max_seq_len)"
            ))
        end
        
        for i in 1:half_dim
            cos_val = rope.cos_cache[pos, i]
            sin_val = rope.sin_cache[pos, i]
            
            q0 = q[b, h, s, i]
            q1 = q[b, h, s, i + half_dim]
            q[b, h, s, i] = q0 * cos_val - q1 * sin_val
            q[b, h, s, i + half_dim] = q0 * sin_val + q1 * cos_val
            
            k0 = k[b, h, s, i]
            k1 = k[b, h, s, i + half_dim]
            k[b, h, s, i] = k0 * cos_val - k1 * sin_val
            k[b, h, s, i + half_dim] = k0 * sin_val + k1 * cos_val
        end
    end
end
