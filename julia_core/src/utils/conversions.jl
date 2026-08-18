"""
Data Conversion Utilities
"""

"""
    to_float32(data)

Convert any numeric array or scalar to Float32.
"""
to_float32(x::Number) = Float32(x)
function to_float32(data::AbstractArray{T}) where T <: Number
    return convert(Array{Float32}, data)
end

"""
    to_float16(data)

Convert any numeric array or scalar to Float16.
"""
to_float16(x::Number) = Float16(x)
function to_float16(data::AbstractArray{T}) where T <: Number
    return convert(Array{Float16}, data)
end


"""
    to_bfloat16(data)

Convert Float32 array to BFloat16 representation (stored as UInt16).
"""
function to_bfloat16(data::AbstractArray{Float32})
    result = similar(data, UInt16)
    @inbounds @simd for i in eachindex(data)
        bits = reinterpret(UInt32, data[i])
        result[i] = UInt16(bits >> 16)
    end
    return result
end

"""
    from_bfloat16(data)

Convert from BFloat16 representation (stored as UInt16) to Float32.
"""
function from_bfloat16(data::AbstractArray{UInt16})
    result = similar(data, Float32)
    @inbounds @simd for i in eachindex(data)
        bits = UInt32(data[i]) << 16
        result[i] = reinterpret(Float32, bits)
    end
    return result
end
