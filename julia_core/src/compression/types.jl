"""
Compression Types & Stats
"""

struct CompressionStats
    original_size::Int
    compressed_size::Int
    ratio::Float64
    time_ns::UInt64
end
