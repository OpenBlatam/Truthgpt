"""Backward compatibility — moved to utils.gpu.kernel_fusion"""
try:
    from .gpu.kernel_fusion import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from gpu.kernel_fusion import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.gpu.kernel_fusion import *  # noqa: F401,F403
