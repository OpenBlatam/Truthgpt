"""
Optimization Loss Functions

Numerically stable cross-entropy, focal loss, and softmax.
"""

"""
    cross_entropy(logits, targets)

Compute numerically stable cross-entropy loss.
"""
function cross_entropy(logits::AbstractMatrix{T}, targets::AbstractVector{<:Integer}) where T
    n_classes, batch_size = size(logits)
    
    if length(targets) != batch_size
        throw(DimensionMismatch(
            "targets length $(length(targets)) must match batch_size $batch_size"
        ))
    end
    if any(t -> t < 1 || t > n_classes, targets)
        throw(ArgumentError("Target indices must be in [1, $n_classes]"))
    end
    
    max_logits = maximum(logits, dims=1)
    shifted = logits .- max_logits
    log_sum_exp = log.(sum(exp.(shifted), dims=1) .+ eps(T))
    log_probs = shifted .- log_sum_exp
    
    loss = zero(T)
    @inbounds @simd for i in 1:batch_size
        loss -= log_probs[targets[i], i]
    end
    
    return loss / batch_size
end

"""
    focal_loss(logits, targets; gamma=2.0, alpha=0.25)

Compute focal loss for imbalanced classification.
"""
function focal_loss(
    logits::AbstractMatrix{T},
    targets::AbstractVector{<:Integer};
    gamma::T = T(DEFAULT_FOCAL_GAMMA),
    alpha::T = T(DEFAULT_FOCAL_ALPHA)
) where T
    n_classes, batch_size = size(logits)
    
    if length(targets) != batch_size
        throw(DimensionMismatch(
            "targets length $(length(targets)) must match batch_size $batch_size"
        ))
    end
    if any(t -> t < 1 || t > n_classes, targets)
        throw(ArgumentError("Target indices must be in [1, $n_classes]"))
    end
    if gamma < 0.0
        throw(ArgumentError("gamma must be non-negative, got $gamma"))
    end
    if alpha < 0.0 || alpha > 1.0
        throw(ArgumentError("alpha must be in [0, 1], got $alpha"))
    end
    
    probs = softmax(logits)
    loss = zero(T)
    eps_val = eps(T)
    
    @inbounds @simd for i in 1:batch_size
        p = probs[targets[i], i]
        p = max(eps_val, min(1.0 - eps_val, p))
        focal_weight = (1.0 - p)^gamma
        loss -= alpha * focal_weight * log(p)
    end
    
    return loss / batch_size
end

"""
    softmax(x; dims=1)

Compute numerically stable softmax along specified dimension.
"""
function softmax(x::AbstractArray{T}; dims=1) where T
    max_x = maximum(x, dims=dims)
    exp_x = exp.(x .- max_x)
    return exp_x ./ (sum(exp_x, dims=dims) .+ eps(T))
end
