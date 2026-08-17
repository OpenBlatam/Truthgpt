"""
Random & Weight Initialization Utilities

Distribution samplers and Xavier / He initialization.
"""

"""
    random_normal(dims...; μ=0.0f0, σ=1.0f0)

Create array of normally distributed random numbers.
"""
function random_normal(dims...; μ::Float32 = 0.0f0, σ::Float32 = 1.0f0)
    if σ < 0.0f0
        throw(ArgumentError("Standard deviation σ must be non-negative, got $σ"))
    end
    return randn(Float32, dims...) .* σ .+ μ
end

"""
    random_uniform(dims...; low=0.0f0, high=1.0f0)

Create array of uniformly distributed random numbers.
"""
function random_uniform(dims...; low::Float32 = 0.0f0, high::Float32 = 1.0f0)
    if low >= high
        throw(ArgumentError("low ($low) must be < high ($high)"))
    end
    return rand(Float32, dims...) .* (high - low) .+ low
end

"""
    xavier_init(fan_in, fan_out)

Xavier/Glorot initialization for neural network weights.
"""
function xavier_init(fan_in::Int, fan_out::Int)
    if fan_in <= 0
        throw(ArgumentError("fan_in must be positive, got $fan_in"))
    end
    if fan_out <= 0
        throw(ArgumentError("fan_out must be positive, got $fan_out"))
    end
    
    σ = sqrt(XAVIER_SCALE_FACTOR / (fan_in + fan_out))
    return randn(Float32, fan_out, fan_in) .* σ
end

"""
    he_init(fan_in, fan_out)

He/Kaiming initialization for neural network weights.
"""
function he_init(fan_in::Int, fan_out::Int)
    if fan_in <= 0
        throw(ArgumentError("fan_in must be positive, got $fan_in"))
    end
    if fan_out <= 0
        throw(ArgumentError("fan_out must be positive, got $fan_out"))
    end
    
    σ = sqrt(HE_SCALE_FACTOR / fan_in)
    return randn(Float32, fan_out, fan_in) .* σ
end
