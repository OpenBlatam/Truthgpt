"""
Cache Constants

Configuration defaults and eviction weighting constants.
"""

# Default configuration values
const DEFAULT_MAX_ENTRIES = 8192
const DEFAULT_COMPRESSION_THRESHOLD = 1024
const DEFAULT_NUM_SHARDS = 16

# Adaptive eviction weights
const ADAPTIVE_AGE_WEIGHT = 0.7
const ADAPTIVE_FREQ_WEIGHT = 0.3
