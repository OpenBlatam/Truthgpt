"""
Timing Utilities

High-resolution timing, benchmarking with warmup, and formatting.
"""

"""
    @timed_block name expr

Execute expression and print timing information.
"""
macro timed_block(name, expr)
    quote
        local start_time = time_ns()
        local result = $(esc(expr))
        local elapsed_ns = time_ns() - start_time
        local elapsed_ms = elapsed_ns / NANOSECONDS_PER_MILLISECOND
        @info "[$($name)] $(round(elapsed_ms, digits=2))ms"
        result
    end
end

"""
    benchmark(f, args...; iterations=100, warmup=10)

Benchmark a function with warmup iterations to ensure JIT compilation.
"""
function benchmark(
    f::Function,
    args...;
    iterations::Int = DEFAULT_BENCHMARK_ITERATIONS,
    warmup::Int = DEFAULT_BENCHMARK_WARMUP
)
    if iterations <= 0
        throw(ArgumentError("iterations must be positive, got $iterations"))
    end
    if warmup < 0
        throw(ArgumentError("warmup must be non-negative, got $warmup"))
    end
    
    for _ in 1:warmup
        f(args...)
    end
    
    times = Vector{Float64}(undef, iterations)
    for i in 1:iterations
        start = time_ns()
        f(args...)
        times[i] = Float64(time_ns() - start)
    end
    
    return (
        mean = mean(times),
        std = std(times),
        min = minimum(times),
        max = maximum(times)
    )
end

"""
    format_time(ns)

Format nanoseconds as human-readable string with appropriate units.
"""
function format_time(ns::Number)
    if ns < 0
        throw(ArgumentError("Time cannot be negative, got $ns"))
    end
    
    if ns < NANOSECONDS_PER_MICROSECOND
        return "$(round(ns, digits=1))ns"
    elseif ns < NANOSECONDS_PER_MILLISECOND
        return "$(round(ns / NANOSECONDS_PER_MICROSECOND, digits=2))μs"
    elseif ns < NANOSECONDS_PER_SECOND
        return "$(round(ns / NANOSECONDS_PER_MILLISECOND, digits=2))ms"
    else
        return "$(round(ns / NANOSECONDS_PER_SECOND, digits=2))s"
    end
end
