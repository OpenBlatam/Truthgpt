"""
Cache Validation

Validation helpers for cache configuration parameters.
"""

"""
    validate_cache_config(max_entries, compression_threshold)

Validate cache configuration parameters.
"""
function validate_cache_config(
    max_entries::Int,
    compression_threshold::Int
)
    validate_max_entries(max_entries)
    validate_compression_threshold(compression_threshold)
end

"""
    validate_max_entries(max_entries)

Validate maximum number of cache entries.
"""
function validate_max_entries(max_entries::Int)
    if max_entries <= 0
        throw(ArgumentError("max_entries must be positive, got $max_entries"))
    end
end

"""
    validate_compression_threshold(compression_threshold)

Validate compression threshold.
"""
function validate_compression_threshold(compression_threshold::Int)
    if compression_threshold <= 0
        throw(ArgumentError(
            "compression_threshold must be positive, got $compression_threshold"
        ))
    end
end
