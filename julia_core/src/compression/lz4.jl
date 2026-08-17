"""
LZ4 Compression Implementation (~5 GB/s)
"""

using CodecLz4

"""
    compress_lz4(data::Vector{UInt8})::Tuple{Vector{UInt8}, CompressionStats}
"""
function compress_lz4(data::Vector{UInt8})::Tuple{Vector{UInt8}, CompressionStats}
    start = time_ns()
    compressed = transcode(LZ4Compressor, data)
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
    decompress_lz4(data::Vector{UInt8})::Vector{UInt8}
"""
function decompress_lz4(data::Vector{UInt8})::Vector{UInt8}
    return transcode(LZ4Decompressor, data)
end
