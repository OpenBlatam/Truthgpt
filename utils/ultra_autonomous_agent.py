"""Backward compatibility — moved to utils.ai.ultra_autonomous_agent"""
try:
    from .ai.ultra_autonomous_agent import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from ai.ultra_autonomous_agent import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.ai.ultra_autonomous_agent import *  # noqa: F401,F403
