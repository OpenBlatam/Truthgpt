"""
Training Tools Module

Utilities for training monitoring, checkpoint visualization,
run comparison, and cleanup.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'visualize_checkpoints',
    'summarize_run',
    'compare_runs',
    'get_run_info',
    'monitor_training',
    'cleanup_runs',
    'plot_loss_curves',
    'visualize_memory_profile',
    'list_available_training_tools',
    'get_training_tool_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'visualize_checkpoints': '..visualize_training',
    'summarize_run': '..visualize_training',
    'plot_loss_curves': '..visualize_training',
    'visualize_memory_profile': '..visualize_training',
    'compare_runs': '..compare_runs',
    'get_run_info': '..compare_runs',
    'monitor_training': '..monitor_training',
    'cleanup_runs': '..cleanup_runs',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_training_tools() -> List[str]:
    """List all available training tools."""
    return _loader.list_components()


def get_training_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get information about a training tool."""
    return _loader.get_component_info(tool_name)
