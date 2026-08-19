"""Backward compatibility — moved to utils.enterprise.truthgpt_adapter"""
try:
    from .enterprise.truthgpt_adapter import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from enterprise.truthgpt_adapter import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.enterprise.truthgpt_adapter import *  # noqa: F401,F403
