"""Backward compatibility — moved to utils.training.advanced_evaluation"""
try:
    from .training.advanced_evaluation import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from training.advanced_evaluation import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.training.advanced_evaluation import *  # noqa: F401,F403
