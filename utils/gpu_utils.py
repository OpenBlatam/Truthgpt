"""Backward compatibility — moved to utils.gpu.gpu_utils"""
try:
    from .gpu.gpu_utils import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from gpu.gpu_utils import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.gpu.gpu_utils import *  # noqa: F401,F403
