"""Backward compatibility — moved to utils.ai.ultra_ml_optimizer"""
try:
    from .ai.ultra_ml_optimizer import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from ai.ultra_ml_optimizer import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.ai.ultra_ml_optimizer import *  # noqa: F401,F403
