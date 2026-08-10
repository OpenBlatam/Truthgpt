"""
Utility Functions for Optimization Core Factories
=================================================
Helpers for dynamic imports, hardware capabilities inspection, argument reflection,
parameter validation, and parameter filtering.
"""

import importlib
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def safe_import(module_name: str) -> Optional[Any]:
    """
    Safely import a Python module by name, returning None if unavailable.

    Args:
        module_name: Dot-separated module path string.

    Returns:
        Imported module object or None if ImportError occurs.
    """
    try:
        return importlib.import_module(module_name)
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return None


def has_package(package_name: str) -> bool:
    """
    Check if a third-party package is installed and importable in the current environment.
    """
    return safe_import(package_name) is not None


def inspect_callable_args(fn: Callable[..., Any]) -> List[str]:
    """
    Retrieve parameter names for a given callable.
    """
    try:
        sig = inspect.signature(fn)
        return list(sig.parameters.keys())
    except (ValueError, TypeError):
        return []


def validate_callable_args(
    fn: Callable[..., Any], kwargs: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Check if required positional/keyword parameters for a callable are present in kwargs.

    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    try:
        sig = inspect.signature(fn)
        missing = []
        for param_name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty and param.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                if param_name not in kwargs:
                    missing.append(param_name)
        return len(missing) == 0, missing
    except (ValueError, TypeError):
        return True, []


def filter_valid_kwargs(
    fn: Callable[..., Any], kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Filter kwargs dictionary to only include keys accepted by fn signature,
    unless fn accepts **kwargs.
    """
    try:
        sig = inspect.signature(fn)
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        if has_var_keyword:
            return kwargs

        valid_params = set(sig.parameters.keys())
        return {k: v for k, v in kwargs.items() if k in valid_params}
    except (ValueError, TypeError):
        return kwargs


def detect_hardware_capabilities() -> Dict[str, Any]:
    """
    Inspect host system hardware capabilities (CUDA, ROCm/MPS, BF16, FP8, Triton, FlashAttention, xFormers, SageAttention).
    """
    torch = safe_import("torch")
    cuda_available = torch.cuda.is_available() if torch else False
    bf16_supported = False
    fp8_supported = False
    cuda_version = None
    device_count = 0
    device_name = "CPU"
    compute_capability = (0, 0)

    if torch and cuda_available:
        try:
            device_count = torch.cuda.device_count()
            if device_count > 0:
                device_name = torch.cuda.get_device_name(0)
                compute_capability = torch.cuda.get_device_capability(0)
            bf16_supported = getattr(torch.cuda, "is_bf16_supported", lambda: False)()
            cuda_version = getattr(torch.version, "cuda", None)
            fp8_supported = compute_capability[0] >= 8 and hasattr(
                torch, "float8_e4m3fn"
            )
        except Exception as e:
            logger.debug(f"Error inspecting CUDA capabilities: {e}")

    has_triton = has_package("triton")
    has_flash = has_package("flash_attn")
    has_xformers = has_package("xformers")
    has_sage = has_package("sageattention")
    has_transformers = has_package("transformers")
    has_bitsandbytes = has_package("bitsandbytes")
    has_deepspeed = has_package("deepspeed")

    return {
        "cuda_available": cuda_available,
        "device_count": device_count,
        "device_name": device_name,
        "cuda_version": cuda_version,
        "compute_capability": compute_capability,
        "bf16_supported": bf16_supported,
        "fp8_supported": fp8_supported,
        "triton_available": has_triton,
        "flash_attn_available": has_flash,
        "xformers_available": has_xformers,
        "sage_attn_available": has_sage,
        "transformers_available": has_transformers,
        "bitsandbytes_available": has_bitsandbytes,
        "deepspeed_available": has_deepspeed,
    }


__all__ = [
    "safe_import",
    "has_package",
    "inspect_callable_args",
    "validate_callable_args",
    "filter_valid_kwargs",
    "detect_hardware_capabilities",
]
