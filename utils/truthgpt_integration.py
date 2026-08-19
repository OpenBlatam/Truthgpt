"""Backward compatibility — moved to utils.truthgpt.integration"""
try:
    from .truthgpt.integration import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from truthgpt.integration import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.truthgpt.integration import *  # noqa: F401,F403
