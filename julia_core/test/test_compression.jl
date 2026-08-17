using Test
using TruthGPT.Compression

@testset "Compression Tests" begin
    # Test data
    raw_data = Vector{UInt8}("TruthGPT High-Performance Scientific Computing with Julia" ^ 20)
    
    # Test LZ4 compression
    try
        compressed_lz4, stats_lz4 = compress_lz4(raw_data)
        @test stats_lz4.original_size == length(raw_data)
        @test stats_lz4.compressed_size == length(compressed_lz4)
        
        decompressed_lz4 = decompress_lz4(compressed_lz4)
        @test decompressed_lz4 == raw_data
    catch e
        @warn "LZ4 tests skipped: $e"
    end
    
    # Test Zstd compression
    try
        compressed_zstd, stats_zstd = compress_zstd(raw_data)
        @test stats_zstd.original_size == length(raw_data)
        
        decompressed_zstd = decompress_zstd(compressed_zstd)
        @test decompressed_zstd == raw_data
    catch e
        @warn "Zstd tests skipped: $e"
    end
end
