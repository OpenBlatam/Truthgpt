"""Backward compatibility — moved to utils.training.advanced_training"""
try:
    from .training.advanced_training import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from training.advanced_training import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.training.advanced_training import *  # noqa: F401,F403
