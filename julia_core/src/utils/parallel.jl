"""
Parallel Computation Utilities

Multi-threaded map and reduce chunk operations.
"""

"""
    parallel_map(f, data; chunk_size=1000)

Apply function f to data in parallel chunks using multiple threads.
"""
function parallel_map(f::Function, data::AbstractVector; chunk_size::Int = DEFAULT_CHUNK_SIZE)
    n = length(data)
    
    if n == 0
        return similar(data)
    end
    
    if chunk_size <= 0
        throw(ArgumentError("chunk_size must be positive, got $chunk_size"))
    end
    
    result_type = typeof(f(data[1]))
    results = Vector{result_type}(undef, n)
    
    Threads.@threads for i in 1:chunk_size:n
        chunk_end = min(i + chunk_size - 1, n)
        @inbounds for j in i:chunk_end
            results[j] = f(data[j])
        end
    end
    
    return results
end

"""
    parallel_reduce(f, op, data; chunk_size=1000)

Apply function f and reduce with operator op in parallel.
"""
function parallel_reduce(
    f::Function,
    op::Function,
    data::AbstractVector;
    chunk_size::Int = DEFAULT_CHUNK_SIZE
)
    n = length(data)
    
    if n == 0
        throw(ArgumentError("Cannot reduce empty vector"))
    end
    
    if chunk_size <= 0
        throw(ArgumentError("chunk_size must be positive, got $chunk_size"))
    end
    
    nchunks = cld(n, chunk_size)
    result_type = typeof(f(data[1]))
    partial_results = Vector{result_type}(undef, nchunks)
    
    Threads.@threads for chunk_idx in 1:nchunks
        start_idx = (chunk_idx - 1) * chunk_size + 1
        end_idx = min(chunk_idx * chunk_size, n)
        
        acc = f(data[start_idx])
        @inbounds for i in (start_idx + 1):end_idx
            acc = op(acc, f(data[i]))
        end
        
        partial_results[chunk_idx] = acc
    end
    
    return reduce(op, partial_results)
end
