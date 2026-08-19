"""Backward compatibility — moved to utils.gpu.cuda_kernels"""
try:
    from .gpu.cuda_kernels import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from gpu.cuda_kernels import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.gpu.cuda_kernels import *  # noqa: F401,F403
