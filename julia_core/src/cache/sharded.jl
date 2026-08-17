"""
Sharded KV Cache

Concurrent partitioned cache with consistent key hashing.
"""

"""
    ShardedKVCache{T}(config::CacheConfig; num_shards::Int=16)

Create a sharded cache with multiple shards.
"""
function ShardedKVCache{T}(
    config::CacheConfig;
    num_shards::Int = DEFAULT_NUM_SHARDS
) where T
    if num_shards <= 0
        throw(ArgumentError("num_shards must be positive, got $num_shards"))
    end
    
    shard_max_entries = cld(config.max_entries, num_shards)
    shard_config = CacheConfig(
        max_entries = shard_max_entries,
        enable_compression = config.enable_compression,
        compression_threshold = config.compression_threshold,
        eviction_strategy = config.eviction_strategy
    )
    
    shards = [KVCache{T}(shard_config) for _ in 1:num_shards]
    return ShardedKVCache(shards, num_shards)
end

"""
    get_shard(cache, layer_idx, position)

Get the shard for a given key using consistent hashing.
"""
function get_shard(cache::ShardedKVCache, layer_idx::Int, position::Int)
    key = make_cache_key(layer_idx, position)
    hash_val = hash(key)
    shard_idx = mod1(hash_val, cache.num_shards)
    return cache.shards[shard_idx]
end

"""
    kv_cache_get(cache::ShardedKVCache, layer_idx, position)

Get cached value from sharded cache.
"""
function kv_cache_get(cache::ShardedKVCache{T}, layer_idx::Int, position::Int) where T
    shard = get_shard(cache, layer_idx, position)
    return kv_cache_get(shard, layer_idx, position)
end

"""
    kv_cache_put(cache::ShardedKVCache, layer_idx, position, data)

Store value in sharded cache.
"""
function kv_cache_put(
    cache::ShardedKVCache{T},
    layer_idx::Int,
    position::Int,
    data::Vector{T}
) where T
    shard = get_shard(cache, layer_idx, position)
    kv_cache_put(shard, layer_idx, position, data)
end

"""
    stats(cache::ShardedKVCache)

Get aggregated statistics from all shards.
"""
function stats(cache::ShardedKVCache)
    total_stats = Dict(
        "entries" => 0,
        "hits" => 0,
        "misses" => 0,
        "evictions" => 0,
        "num_shards" => cache.num_shards,
        "max_entries" => 0
    )
    
    @inbounds for shard in cache.shards
        shard_stats = stats(shard)
        total_stats["entries"] += shard_stats["entries"]
        total_stats["hits"] += shard_stats["hits"]
        total_stats["misses"] += shard_stats["misses"]
        total_stats["evictions"] += shard_stats["evictions"]
        total_stats["max_entries"] += shard_stats["max_entries"]
    end
    
    total_requests = total_stats["hits"] + total_stats["misses"]
    total_stats["hit_rate"] = total_requests > 0 ? 
        Float64(total_stats["hits"]) / Float64(total_requests) : 0.0
    
    total_stats["utilization"] = total_stats["max_entries"] > 0 ?
        total_stats["entries"] / total_stats["max_entries"] : 0.0
    
    return total_stats
end
