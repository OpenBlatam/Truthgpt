"""Backward compatibility — moved to utils.ai.ai_utils"""
try:
    from .ai.ai_utils import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from ai.ai_utils import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.ai.ai_utils import *  # noqa: F401,F403
