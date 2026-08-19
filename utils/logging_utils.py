"""Backward compatibility — moved to utils.logging.basic"""
try:
    from .logging.basic import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from logging.basic import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.logging.basic import *  # noqa: F401,F403
