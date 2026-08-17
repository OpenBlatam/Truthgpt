"""
TruthGPT Compression Submodule

LZ4 and Zstd high-throughput compression utilities.
"""
module Compression

using CodecLz4
using CodecZstd

export compress_lz4, decompress_lz4, compress_zstd, decompress_zstd
export CompressionStats

struct CompressionStats
    original_size::Int
    compressed_size::Int
    ratio::Float64
    time_ns::UInt64
end

"""
    compress_lz4(data)

LZ4 compression (~5 GB/s).
"""
function compress_lz4(data::Vector{UInt8})::Tuple{Vector{UInt8}, CompressionStats}
    start = time_ns()
    compressed = transcode(LZ4Compressor, data)
    elapsed = time_ns() - start
    
    stats = CompressionStats(
        length(data),
        length(compressed),
        length(compressed) / length(data),
        elapsed
    )
    
    return (compressed, stats)
end

function decompress_lz4(data::Vector{UInt8})::Vector{UInt8}
    return transcode(LZ4Decompressor, data)
end

"""
    compress_zstd(data; level=3)

Zstd compression (balanced speed/ratio).
"""
function compress_zstd(data::Vector{UInt8}; level::Int=3)::Tuple{Vector{UInt8}, CompressionStats}
    start = time_ns()
    compressed = transcode(ZstdCompressor(; level=level), data)
    elapsed = time_ns() - start
    
    stats = CompressionStats(
        length(data),
        length(compressed),
        length(compressed) / length(data),
        elapsed
    )
    
    return (compressed, stats)
end

function decompress_zstd(data::Vector{UInt8})::Vector{UInt8}
    return transcode(ZstdDecompressor, data)
end

end # module Compression
