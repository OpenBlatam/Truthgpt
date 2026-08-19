"""Backward compatibility — moved to utils.ai.neural_architecture_search"""
try:
    from .ai.neural_architecture_search import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from ai.neural_architecture_search import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.ai.neural_architecture_search import *  # noqa: F401,F403
