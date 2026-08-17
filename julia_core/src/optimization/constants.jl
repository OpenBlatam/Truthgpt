"""
Optimization Constants

Default parameter ranges, decay parameters, and numerical tolerances.
"""

# Default hyperparameter ranges
const DEFAULT_LR_MIN = 1e-6
const DEFAULT_LR_MAX = 1e-2
const DEFAULT_BATCH_MIN = 8
const DEFAULT_BATCH_MAX = 128
const DEFAULT_DROPOUT_MIN = 0.0
const DEFAULT_DROPOUT_MAX = 0.5
const DEFAULT_WARMUP_MIN = 100
const DEFAULT_WARMUP_MAX = 2000

# Bayesian optimization parameters
const DEFAULT_BAYESIAN_EXPLORATION_DECAY = 0.01
const DEFAULT_BAYESIAN_MIN_EXPLORATION = 0.1

# Focal loss defaults
const DEFAULT_FOCAL_GAMMA = 2.0
const DEFAULT_FOCAL_ALPHA = 0.25

# Numerical stability constants
const EPS_FLOAT32 = 1e-5f0
const EPS_FLOAT64 = 1e-8

# Optimization method constants
const METHOD_BAYESIAN = :bayesian
const METHOD_RANDOM = :random
const METHOD_GRID = :grid
