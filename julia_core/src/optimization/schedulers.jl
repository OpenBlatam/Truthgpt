"""
Learning Rate Schedulers

Cosine annealing, linear warmup, and warmup + cosine decay schedules.
"""

"""
    cosine_schedule(step, total_steps, lr_max, lr_min=0)

Cosine annealing learning rate schedule.
"""
function cosine_schedule(step::Int, total_steps::Int, lr_max::T, lr_min::T=zero(T)) where T
    if step >= total_steps
        return lr_min
    end
    if total_steps <= 0
        throw(ArgumentError("total_steps must be positive, got $total_steps"))
    end
    
    cosine_factor = (1.0 + cos(π * step / total_steps)) / 2.0
    return lr_min + (lr_max - lr_min) * cosine_factor
end

"""
    warmup_cosine_schedule(step, warmup_steps, total_steps, lr_max)

Warmup + cosine decay schedule.
"""
function warmup_cosine_schedule(
    step::Int,
    warmup_steps::Int,
    total_steps::Int,
    lr_max::T
) where T
    if warmup_steps <= 0
        throw(ArgumentError("warmup_steps must be positive, got $warmup_steps"))
    end
    if total_steps <= warmup_steps
        throw(ArgumentError("total_steps ($total_steps) must be > warmup_steps ($warmup_steps)"))
    end
    
    if step < warmup_steps
        return lr_max * step / warmup_steps
    else
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        cosine_factor = (1.0 + cos(π * progress)) / 2.0
        return lr_max * cosine_factor
    end
end

"""
    linear_warmup(step, warmup_steps, lr_max)

Linear warmup schedule.
"""
function linear_warmup(step::Int, warmup_steps::Int, lr_max::T) where T
    if warmup_steps <= 0
        throw(ArgumentError("warmup_steps must be positive, got $warmup_steps"))
    end
    return min(lr_max, lr_max * step / warmup_steps)
end
