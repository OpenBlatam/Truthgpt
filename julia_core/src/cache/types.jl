"""
Cache Types

Enum definitions and type declarations for single and sharded KV caching.
"""

"""
    EvictionStrategy

Cache eviction strategy enumeration.
- `LRU`: Least Recently Used
- `LFU`: Least Frequently Used
- `FIFO`: First In First Out
- `Adaptive`: Hybrid LRU + LFU with weighted scoring
"""
@enum EvictionStrategy begin
    LRU
    LFU
    FIFO
    Adaptive
end

"""
    CacheConfig

Configuration for KV cache.
"""
struct CacheConfig
    max_entries::Int
    enable_compression::Bool
    compression_threshold::Int
    eviction_strategy::EvictionStrategy
    
    function CacheConfig(
        max_entries::Int = DEFAULT_MAX_ENTRIES,
        enable_compression::Bool = true,
        compression_threshold::Int = DEFAULT_COMPRESSION_THRESHOLD,
        eviction_strategy::EvictionStrategy = LRU
    )
        validate_cache_config(max_entries, compression_threshold)
        new(max_entries, enable_compression, compression_threshold, eviction_strategy)
    end
end

"""
    CacheConfig(; kwargs...)

Create CacheConfig with keyword arguments.
"""
function CacheConfig(;
    max_entries::Int = DEFAULT_MAX_ENTRIES,
    enable_compression::Bool = true,
    compression_threshold::Int = DEFAULT_COMPRESSION_THRESHOLD,
    eviction_strategy::EvictionStrategy = LRU
)
    CacheConfig(max_entries, enable_compression, compression_threshold, eviction_strategy)
end

"""
    CacheEntry{T}

Single cache entry with metadata for eviction decisions.
"""
mutable struct CacheEntry{T}
    data::Vector{T}
    access_count::Int64
    last_access::Float64
    created_at::Float64
    is_compressed::Bool
    original_size::Int
end

"""
    CacheEntry(data::Vector{T})

Create a new CacheEntry with current timestamp.
"""
function CacheEntry(data::Vector{T}) where T
    current_time = time()
    original_size = length(data) * sizeof(T)
    
    CacheEntry(
        data,
        1,              # access_count
        current_time,   # last_access
        current_time,   # created_at
        false,          # is_compressed
        original_size   # original_size
    )
end

"""
    touch!(entry::CacheEntry)

Update access statistics for an entry.
"""
function touch!(entry::CacheEntry)
    entry.access_count += 1
    entry.last_access = time()
end

"""
    KVCache{T}

High-performance KV cache with eviction support and thread-safety.
"""
mutable struct KVCache{T}
    config::CacheConfig
    data::Dict{Tuple{Int, Int}, CacheEntry{T}}
    lock::ReentrantLock
    hits::Threads.Atomic{Int64}
    misses::Threads.Atomic{Int64}
    evictions::Threads.Atomic{Int64}
end

"""
    KVCache{T}(config::CacheConfig=CacheConfig())

Create a new KVCache instance.
"""
function KVCache{T}(config::CacheConfig = CacheConfig()) where T
    KVCache{T}(
        config,
        Dict{Tuple{Int, Int}, CacheEntry{T}}(),
        ReentrantLock(),
        Threads.Atomic{Int64}(0),
        Threads.Atomic{Int64}(0),
        Threads.Atomic{Int64}(0)
    )
end

"""
    ShardedKVCache{T}

Sharded cache for better concurrency.
"""
struct ShardedKVCache{T}
    shards::Vector{KVCache{T}}
    num_shards::Int
end
