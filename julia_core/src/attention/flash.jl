"""
Flash Attention

Memory-efficient block-wise Flash Attention implementation.
"""

"""
    flash_attention(Q, K, V, config)

Memory-efficient Flash Attention implementation.

Uses block-wise computation to reduce memory from O(N²) to O(N).
"""
function flash_attention(
    Q::Array{T, 4},
    K::Array{T, 4},
    V::Array{T, 4},
    config::AttentionConfig
) where T <: AbstractFloat
    validate_attention_inputs(Q, K, V)
    
    batch, heads, seq_q, head_dim = size(Q)
    _, _, seq_k, _ = size(K)
    
    block_size = config.block_size
    s = scale(config)
    
    output = zeros(T, batch, heads, seq_q, head_dim)
    l = zeros(T, batch, heads, seq_q)  # Running sum of exp values
    m = fill(T(NEGATIVE_INFINITY), batch, heads, seq_q)  # Running max
    
    num_blocks_k = cld(seq_k, block_size)
    
    for bk in 1:num_blocks_k
        k_start = (bk - 1) * block_size + 1
        k_end = min(bk * block_size, seq_k)
        k_size = k_end - k_start + 1
        
        K_block = @view K[:, :, k_start:k_end, :]
        V_block = @view V[:, :, k_start:k_end, :]
        
        attn_block = compute_attention_block(Q, K_block, s)
        
        if config.use_causal
            mask_causal_block!(attn_block, k_start)
        end
        
        m_new = maximum(attn_block, dims=4)[:, :, :, 1]
        m_combined = max.(m, m_new)
        
        exp_old = exp.(m .- m_combined)
        exp_new = exp.(attn_block .- reshape(m_combined, batch, heads, seq_q, 1))
        
        l_new = sum(exp_new, dims=4)[:, :, :, 1]
        l .= l .* exp_old .+ l_new
        
        for d in 1:head_dim
            output[:, :, :, d] .= output[:, :, :, d] .* exp_old
            for j in 1:k_size
                output[:, :, :, d] .+= exp_new[:, :, :, j] .* V_block[:, :, j, d]
            end
        end
        
        m .= m_combined
    end
    
    for d in 1:head_dim
        output[:, :, :, d] ./= l
    end
    
    return output
end

"""
    compute_attention_block(Q, K_block, scale)

Compute attention scores for a block of keys.
"""
function compute_attention_block(Q::Array{T, 4}, K_block::Array{T, 4}, scale::T) where T
    batch, heads, seq_q, head_dim = size(Q)
    _, _, k_size, _ = size(K_block)
    
    attn = zeros(T, batch, heads, seq_q, k_size)
    
    @inbounds for b in 1:batch, h in 1:heads, i in 1:seq_q, j in 1:k_size
        sum_qk = zero(T)
        for d in 1:head_dim
            sum_qk += Q[b, h, i, d] * K_block[b, h, j, d]
        end
        attn[b, h, i, j] = sum_qk * scale
    end
    
    return attn
end

"""
    mask_causal_block!(attn, k_start)

Apply causal mask to an attention block in-place.
"""
function mask_causal_block!(attn::Array{T, 4}, k_start::Int) where T
    batch, heads, seq_q, k_size = size(attn)
    
    @inbounds for i in 1:seq_q
        for j in 1:k_size
            global_j = k_start + j - 1
            if global_j > i
                attn[:, :, i, j] .= T(NEGATIVE_INFINITY)
            end
        end
    end
end
