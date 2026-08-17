"""
Utility Module Constants and Types
"""

# Time conversion constants
const NANOSECONDS_PER_MICROSECOND = 1_000
const NANOSECONDS_PER_MILLISECOND = 1_000_000
const NANOSECONDS_PER_SECOND = 1_000_000_000

# Memory conversion constants
const BYTES_PER_KB = 1024
const BYTES_PER_MB = 1024^2
const BYTES_PER_GB = 1024^3
const BYTES_PER_TB = 1024^4

# Numerical stability constants
const DEFAULT_EPSILON = 1e-5f0
const GELU_APPROX_CONST = 0.044715f0
const SQRT_2_OVER_PI = sqrt(2.0f0 / Float32(π))

# Default benchmark parameters
const DEFAULT_BENCHMARK_ITERATIONS = 100
const DEFAULT_BENCHMARK_WARMUP = 10
const DEFAULT_CHUNK_SIZE = 1000

# Weight initialization constants
const XAVIER_SCALE_FACTOR = 2.0f0
const HE_SCALE_FACTOR = 2.0f0
