"""
Configuration utilities re-exporter for optimization_core.
"""

from modules.base.core_system.core.config_utils import (
    load_config,
    save_config,
    merge_configs,
    merge_multiple_configs,
    validate_config,
    get_config_value,
    set_config_value,
    has_config_key,
    flatten_config,
    unflatten_config,
)

__all__ = [
    'load_config',
    'save_config',
    'merge_configs',
    'merge_multiple_configs',
    'validate_config',
    'get_config_value',
    'set_config_value',
    'has_config_key',
    'flatten_config',
    'unflatten_config',
]

