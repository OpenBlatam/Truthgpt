"""Backward compatibility — moved to utils.truthgpt.enhanced_utils"""
try:
    from .truthgpt.enhanced_utils import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from truthgpt.enhanced_utils import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.truthgpt.enhanced_utils import *  # noqa: F401,F403
