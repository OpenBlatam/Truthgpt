"""Enterprise Unified Configuration Manager for Optimization Core.

Provides high-level configuration orchestration, environment variable bindings,
YAML/JSON parser integration, and schema validation utilities.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar, Type

from .schema import (
    AppCfg,
    ModelCfg,
    TrainingCfg,
    InferenceCfg,
    OptimizationCfg,
    AgentOrchestratorCfg,
    BaseOptimizationSchema,
)
from .loader import load_config, save_config, get_preset_config, parse_env_overrides

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseOptimizationSchema)


class UnifiedConfigManager:
    """Enterprise configuration orchestrator with environment variable resolution and caching."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None, env_prefix: str = "OPTIMIZATION_") -> None:
        self.env_prefix = env_prefix
        self.raw_data: Dict[str, Any] = {}
        if config_path and Path(config_path).exists():
            self.raw_data = load_config(config_path)
        
        # Apply environment overrides
        env_overrides = parse_env_overrides(prefix=self.env_prefix)
        self.raw_data.update(env_overrides)
        
        # Instantiate schema
        self._config: AppCfg = AppCfg.from_dict(self.raw_data) if self.raw_data else AppCfg()

    @property
    def config(self) -> AppCfg:
        """Get the active application configuration schema."""
        return self._config

    def update_from_dict(self, updates: Dict[str, Any]) -> AppCfg:
        """Apply dictionary updates and re-validate schema."""
        merged = {**self._config.to_dict(), **updates}
        self._config = AppCfg.from_dict(merged)
        return self._config

    def save(self, target_path: Union[str, Path]) -> None:
        """Persist active configuration to disk."""
        save_config(self._config.to_dict(), target_path)

    @classmethod
    def from_preset(cls, preset_name: str) -> "UnifiedConfigManager":
        """Instantiate configuration manager from a pre-defined system preset."""
        manager = cls()
        preset_dict = get_preset_config(preset_name)
        manager._config = AppCfg.from_dict(preset_dict)
        return manager


__all__ = ["UnifiedConfigManager"]
