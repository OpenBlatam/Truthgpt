"""Backward compatibility — moved to utils.truthgpt.examples"""
try:
    from .truthgpt.examples import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from truthgpt.examples import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.truthgpt.examples import *  # noqa: F401,F403
