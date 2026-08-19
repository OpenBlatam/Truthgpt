"""Backward compatibility — moved to utils.memory.memory_utils"""
try:
    from .memory.memory_utils import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from memory.memory_utils import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.memory.memory_utils import *  # noqa: F401,F403
