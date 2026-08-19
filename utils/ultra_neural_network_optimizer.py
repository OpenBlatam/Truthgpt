"""Backward compatibility — moved to utils.ai.ultra_nn_optimizer"""
try:
    from .ai.ultra_nn_optimizer import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from ai.ultra_nn_optimizer import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.ai.ultra_nn_optimizer import *  # noqa: F401,F403
