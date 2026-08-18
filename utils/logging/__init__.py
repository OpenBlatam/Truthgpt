"""
Logging Utilities Package

Unified logging utilities consolidating basic structured logging
and advanced logging with JSON formatting, rotation, and context.

Basic logging (from .basic):
    - setup_logger() — basic console+file logger
    - get_logger() — get or create logger
    - TrainingLogger — training-specific structured logger

Advanced logging (from .advanced):
    - JSONFormatter — JSON log formatter
    - StructuredLogger — advanced logger with rotating file handlers
    - setup_logging() — create StructuredLogger instances
    - log_info() — rank-aware info logging
    - is_main_process() — distributed rank check
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    # Basic
    'setup_logger',
    'get_logger',
    'TrainingLogger',
    # Advanced
    'JSONFormatter',
    'StructuredLogger',
    'setup_logging',
    'log_info',
    'is_main_process',
    'list_available_logging_components',
    'get_logging_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    # Basic logging
    'setup_logger': '.basic',
    'get_logger': '.basic',
    'TrainingLogger': '.basic',
    # Advanced logging
    'JSONFormatter': '.advanced',
    'StructuredLogger': '.advanced',
    'setup_logging': '.advanced',
    'log_info': '.advanced',
    'is_main_process': '.advanced',
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


def list_available_logging_components() -> List[str]:
    """List all available logging components."""
    return _loader.list_components()


def get_logging_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a logging component."""
    return _loader.get_component_info(component_name)
