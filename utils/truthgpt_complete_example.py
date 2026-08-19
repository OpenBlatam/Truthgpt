"""Backward compatibility — moved to utils.truthgpt.complete_example"""
try:
    from .truthgpt.complete_example import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from truthgpt.complete_example import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.truthgpt.complete_example import *  # noqa: F401,F403
