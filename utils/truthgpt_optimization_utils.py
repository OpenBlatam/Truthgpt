"""Backward compatibility — moved to utils.training.optimization_utils"""
try:
    from .training.optimization_utils import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from training.optimization_utils import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.training.optimization_utils import *  # noqa: F401,F403
