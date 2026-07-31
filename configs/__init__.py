"""
Configs Module

This module provides configuration loading and schema validation.
It works alongside the config/ module which provides configuration classes.
"""

from __future__ import annotations

# Direct imports
from .loader import (
    load_config,
    save_config,
    get_preset_config,
    parse_overrides,
    parse_env_overrides,
    deep_merge,
)
from .unified_config import UnifiedConfigManager
from .schema import (
    BaseOptimizationSchema,
    QuantizationCfg,
    KVCacheCfg,
    CompilerCfg,
    AgentOrchestratorCfg,
    TrainingCfg,
    ModelCfg,
    InferenceCfg,
    OptimizationCfg,
    AppCfg,
)

# Lazy imports for presets
_LAZY_IMPORTS = {
    'presets': '.presets',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for configs submodules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=1)
        _import_cache[name] = module
        return module
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


def list_available_config_modules() -> list[str]:
    """List all available config submodules."""
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    "load_config",
    "save_config",
    "get_preset_config",
    "parse_overrides",
    "parse_env_overrides",
    "deep_merge",
    "BaseOptimizationSchema",
    "QuantizationCfg",
    "KVCacheCfg",
    "CompilerCfg",
    "AgentOrchestratorCfg",
    "TrainingCfg",
    "ModelCfg",
    "InferenceCfg",
    "OptimizationCfg",
    "AppCfg",
    "UnifiedConfigManager",
    "presets",
    "list_available_config_modules",
]


