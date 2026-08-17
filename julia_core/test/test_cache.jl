"""
Unit tests for Cache subsystem
"""

using Test

@testset "Cache Subsystem Tests" begin
    config = TruthGPT.Cache.CacheConfig(max_entries = 100)
    cache = TruthGPT.Cache.KVCache{Float32}(config)
    
    data1 = randn(Float32, 128)
    TruthGPT.Cache.kv_cache_put(cache, 1, 10, data1)
    entry = TruthGPT.Cache.kv_cache_get(cache, 1, 10)
    
    @test !isnothing(entry)
    @test size(entry) == (128,)
    @test entry == data1
    
    miss = TruthGPT.Cache.kv_cache_get(cache, 1, 999)
    @test isnothing(miss)
    
    st = TruthGPT.Cache.stats(cache)
    @test st["entries"] == 1
    @test st["hits"] == 1
    @test st["misses"] == 1
    
    TruthGPT.Cache.clear!(cache)
    @test TruthGPT.Cache.kv_cache_get(cache, 1, 10) === nothing
end
