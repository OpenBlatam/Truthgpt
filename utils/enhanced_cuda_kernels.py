"""Backward compatibility — moved to utils.gpu.enhanced_cuda_kernels"""
try:
    from .gpu.enhanced_cuda_kernels import *  # noqa: F401,F403
except (ImportError, ValueError):
    try:
        from gpu.enhanced_cuda_kernels import *  # noqa: F401,F403
    except (ImportError, ValueError):
        from utils.gpu.enhanced_cuda_kernels import *  # noqa: F401,F403
