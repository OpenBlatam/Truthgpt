"""
Compression Submodule

High-performance data compression utilities for KV cache and tensor streaming.
"""

include("types.jl")
include("lz4.jl")
include("zstd.jl")

export compress_lz4, decompress_lz4, compress_zstd, decompress_zstd
export CompressionStats
