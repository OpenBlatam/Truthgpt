"""
Cache Eviction

Eviction policies and key selection algorithms.
"""

"""
    select_eviction_key(cache)

Select key to evict based on configured eviction strategy.
"""
function select_eviction_key(cache::KVCache)
    isempty(cache.data) && return nothing
    
    strategy = cache.config.eviction_strategy
    
    if strategy == LRU
        return argmin(e -> e.last_access, cache.data)[1]
    elseif strategy == LFU
        return argmin(e -> e.access_count, cache.data)[1]
    elseif strategy == FIFO
        return argmin(e -> e.created_at, cache.data)[1]
    else  # Adaptive
        current_time = time()
        return argmin(cache.data) do (k, e)
            age_score = current_time - e.last_access
            freq_score = 1.0 / (e.access_count + 1)
            ADAPTIVE_AGE_WEIGHT * age_score + ADAPTIVE_FREQ_WEIGHT * freq_score
        end[1]
    end
end

"""
    evict!(cache)

Evict one entry based on configured strategy.
"""
function evict!(cache::KVCache)
    isempty(cache.data) && return 0
    
    key_to_remove = select_eviction_key(cache)
    
    if !isnothing(key_to_remove)
        delete!(cache.data, key_to_remove)
        Threads.atomic_add!(cache.evictions, 1)
        return 1
    end
    
    return 0
end
