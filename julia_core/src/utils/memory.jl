"""
Memory Utilities

Byte formatting and garbage collector statistics.
"""

"""
    format_bytes(bytes)

Format bytes as human-readable string with appropriate units.
"""
function format_bytes(bytes::Integer)
    if bytes < 0
        throw(ArgumentError("bytes must be non-negative, got $bytes"))
    end
    
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 1
    value = Float64(bytes)
    
    while value >= BYTES_PER_KB && idx < length(units)
        value /= BYTES_PER_KB
        idx += 1
    end
    
    return "$(round(value, digits=2)) $(units[idx])"
end

"""
    memory_info()

Get current memory usage information from garbage collector.
"""
function memory_info()
    gc_stats = Base.gc_num()
    return (
        allocated = gc_stats.allocd,
        total_time_ns = gc_stats.total_time,
        num_gc = gc_stats.pause
    )
end
