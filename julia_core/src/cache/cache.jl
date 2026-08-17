"""
Cache Module

High-Performance KV Cache for TruthGPT with multiple eviction strategies
and concurrent sharded access patterns.
"""

using Base.Threads
using Random

include("constants.jl")
include("types.jl")
include("validation.jl")
include("eviction.jl")
include("kv_cache.jl")
include("sharded.jl")

export EvictionStrategy, LRU, LFU, FIFO, Adaptive
export CacheConfig, KVCache, ShardedKVCache
export kv_cache_get, kv_cache_put, clear!, hit_rate, stats
