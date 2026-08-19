"""Backward compatibility — moved to utils.truthgpt.core"""
try:
    from .truthgpt.core import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from truthgpt.core import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.truthgpt.core import *  # noqa: F401,F403
