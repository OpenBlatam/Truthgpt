"""Backward compatibility — moved to utils.monitoring.observability"""
try:
    from .monitoring.observability import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from monitoring.observability import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.monitoring.observability import *  # noqa: F401,F403
