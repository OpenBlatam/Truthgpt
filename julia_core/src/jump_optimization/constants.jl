"""
JuMP Optimization Constants

Solver options, tolerances, and status mappings.
"""

# Solver options
const DEFAULT_SOLVER = HiGHS.Optimizer

# Numerical tolerances
const SYMMETRY_TOLERANCE = 1e-10

# Optimization status constants
const STATUS_OPTIMAL = OPTIMAL
