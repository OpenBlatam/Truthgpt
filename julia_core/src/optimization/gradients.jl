"""
Gradient Operations

Gradient norm clipping and accumulation routines.
"""

"""
    clip_grad_norm!(grads, max_norm)

Clip gradient norm in-place to prevent exploding gradients.
"""
function clip_grad_norm!(grads::AbstractArray, max_norm::Real)
    if max_norm <= 0.0
        throw(ArgumentError("max_norm must be positive, got $max_norm"))
    end
    
    total_norm_sq = zero(typeof(max_norm))
    
    for g in grads
        if g isa AbstractArray
            total_norm_sq += sum(abs2, g)
        end
    end
    
    total_norm = sqrt(total_norm_sq)
    
    if total_norm > max_norm
        scale_val = max_norm / (total_norm + eps(typeof(max_norm)))
        for g in grads
            if g isa AbstractArray
                g .*= scale_val
            end
        end
    end
    
    return total_norm
end

"""
    gradient_accumulate!(accum, grads, scale=1)

Accumulate scaled gradients into accumulator.
"""
function gradient_accumulate!(accum::AbstractArray, grads::AbstractArray, scale::Real=1)
    if length(accum) != length(grads)
        throw(DimensionMismatch(
            "accum and grads must have same length, got $(length(accum)) and $(length(grads))"
        ))
    end
    
    @inbounds for i in 1:length(accum)
        if accum[i] isa AbstractArray && grads[i] isa AbstractArray
            accum[i] .+= scale .* grads[i]
        end
    end
end
