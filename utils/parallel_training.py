"""Backward compatibility — moved to utils.training.parallel_training"""
try:
    from .training.parallel_training import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from training.parallel_training import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.training.parallel_training import *  # noqa: F401,F403
