"""
KV Cache Core Operations

Get, put, clear, and statistics for KVCache.
"""

"""
    make_cache_key(layer_idx, position)

Create a cache key tuple.
"""
@inline make_cache_key(layer_idx::Int, position::Int) = (layer_idx, position)

"""
    kv_cache_get(cache, layer_idx, position)

Get cached value for given layer and position.
"""
function kv_cache_get(cache::KVCache{T}, layer_idx::Int, position::Int) where T
    key = make_cache_key(layer_idx, position)
    
    lock(cache.lock) do
        if haskey(cache.data, key)
            entry = cache.data[key]
            touch!(entry)
            Threads.atomic_add!(cache.hits, 1)
            return copy(entry.data)
        else
            Threads.atomic_add!(cache.misses, 1)
            return nothing
        end
    end
end

"""
    kv_cache_put(cache, layer_idx, position, data)

Store value in cache, evicting entries if capacity is reached.
"""
function kv_cache_put(
    cache::KVCache{T},
    layer_idx::Int,
    position::Int,
    data::Vector{T}
) where T
    if isempty(data)
        throw(ArgumentError("Cannot cache empty data"))
    end
    
    key = make_cache_key(layer_idx, position)
    
    lock(cache.lock) do
        while length(cache.data) >= cache.config.max_entries
            evict!(cache)
        end
        cache.data[key] = CacheEntry(data)
    end
end

"""
    clear!(cache)

Clear all cached data and reset statistics.
"""
function clear!(cache::KVCache)
    lock(cache.lock) do
        empty!(cache.data)
        
        hits_val = cache.hits[]
        misses_val = cache.misses[]
        evictions_val = cache.evictions[]
        
        Threads.atomic_sub!(cache.hits, hits_val)
        Threads.atomic_sub!(cache.misses, misses_val)
        Threads.atomic_sub!(cache.evictions, evictions_val)
    end
end

"""
    Base.length(cache::KVCache)

Get number of cached entries.
"""
Base.length(cache::KVCache) = length(cache.data)

"""
    hit_rate(cache::KVCache)

Get cache hit rate as a ratio.
"""
function hit_rate(cache::KVCache)
    hits = cache.hits[]
    misses = cache.misses[]
    total = hits + misses
    return total > 0 ? Float64(hits) / Float64(total) : 0.0
end

"""
    stats(cache::KVCache)

Get comprehensive cache statistics.
"""
function stats(cache::KVCache)
    hits_val = cache.hits[]
    misses_val = cache.misses[]
    evictions_val = cache.evictions[]
    entries_count = length(cache.data)
    
    total_requests = hits_val + misses_val
    hit_rate_val = total_requests > 0 ? Float64(hits_val) / Float64(total_requests) : 0.0
    
    return Dict(
        "entries" => entries_count,
        "max_entries" => cache.config.max_entries,
        "hits" => hits_val,
        "misses" => misses_val,
        "evictions" => evictions_val,
        "hit_rate" => hit_rate_val,
        "utilization" => entries_count / cache.config.max_entries
    )
end
