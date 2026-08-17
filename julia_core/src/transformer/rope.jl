"""
Rotary Position Embeddings (RoPE) for Transformer
"""

using LinearAlgebra

"""
    precompute_rope_freqs(dim, max_seq_len; base=10000.0)

Precompute RoPE frequency matrices.
"""
function precompute_rope_freqs(
    dim::Int,
    max_seq_len::Int;
    base::Float32 = DEFAULT_ROPE_BASE
)
    if dim <= 0 || dim % 2 != 0
        throw(ArgumentError("dim must be positive and even, got $dim"))
    end
    if max_seq_len <= 0
        throw(ArgumentError("max_seq_len must be positive, got $max_seq_len"))
    end
    
    inv_freq = 1.0f0 ./ (base .^ (Float32.(0:2:dim-1) ./ dim))
    positions = Float32.(0:max_seq_len-1)
    freqs = positions * inv_freq'
    
    cos_cache = cos.(freqs)
    sin_cache = sin.(freqs)
    
    return cos_cache, sin_cache
end

"""
    apply_rope(q, k, cos_cache, sin_cache; start_pos=0)

Apply rotary position embeddings to Q and K tensors.
"""
function apply_rope(
    q::Array{Float32, 3},
    k::Array{Float32, 3},
    cos_cache::Matrix{Float32},
    sin_cache::Matrix{Float32};
    start_pos::Int = 0
)
    batch, seq_len, d_head = size(q)
    
    if size(k) != size(q)
        throw(DimensionMismatch("Q and K must have same shape"))
    end
    if d_head % 2 != 0
        throw(ArgumentError("d_head must be even, got $d_head"))
    end
    
    half_dim = d_head ÷ 2
    q_rotated = similar(q)
    k_rotated = similar(k)
    
    @inbounds for b in 1:batch, s in 1:seq_len
        pos = start_pos + s
        
        if pos > size(cos_cache, 1)
            throw(ArgumentError(
                "Position $pos exceeds cache size $(size(cos_cache, 1))"
            ))
        end
        
        for i in 1:half_dim
            cos_θ = cos_cache[pos, i]
            sin_θ = sin_cache[pos, i]
            
            q0, q1 = q[b, s, i], q[b, s, i + half_dim]
            q_rotated[b, s, i] = q0 * cos_θ - q1 * sin_θ
            q_rotated[b, s, i + half_dim] = q0 * sin_θ + q1 * cos_θ
            
            k0, k1 = k[b, s, i], k[b, s, i + half_dim]
            k_rotated[b, s, i] = k0 * cos_θ - k1 * sin_θ
            k_rotated[b, s, i + half_dim] = k0 * sin_θ + k1 * cos_θ
        end
    end
    
    return q_rotated, k_rotated
end
