"""Backward compatibility — moved to utils.logging.advanced"""
try:
    from .logging.advanced import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from logging.advanced import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.logging.advanced import *  # noqa: F401,F403
