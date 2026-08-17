"""
Zstd Compression Implementation (Balanced speed/ratio)
"""

using CodecZstd

"""
    compress_zstd(data::Vector{UInt8}; level::Int=3)::Tuple{Vector{UInt8}, CompressionStats}
"""
function compress_zstd(data::Vector{UInt8}; level::Int=3)::Tuple{Vector{UInt8}, CompressionStats}
    start = time_ns()
    compressed = transcode(ZstdCompressor(; level=level), data)
    elapsed = time_ns() - start
    
    stats = CompressionStats(
        length(data),
        length(compressed),
        length(data) > 0 ? length(compressed) / length(data) : 1.0,
        elapsed
    )
    
    return (compressed, stats)
end

"""
    decompress_zstd(data::Vector{UInt8})::Vector{UInt8}
"""
function decompress_zstd(data::Vector{UInt8})::Vector{UInt8}
    return transcode(ZstdDecompressor, data)
end
