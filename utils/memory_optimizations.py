"""Backward compatibility — moved to utils.memory.optimizations"""
try:
    from .memory.optimizations import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from memory.optimizations import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.memory.optimizations import *  # noqa: F401,F403
