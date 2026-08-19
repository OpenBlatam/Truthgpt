"""Backward compatibility — moved to utils.memory.pooling"""
try:
    from .memory.pooling import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from memory.pooling import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.memory.pooling import *  # noqa: F401,F403
