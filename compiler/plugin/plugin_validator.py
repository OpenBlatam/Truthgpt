"""
Plugin Validator module for TruthGPT Compiler
Validation and compatibility checking for compiler plugins
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager

from .plugin_system import CompilerPlugin

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when plugin validation fails."""
    pass


@dataclass
class ValidationResult:
    """Result of plugin validation checks."""
    is_valid: bool
    plugin_name: str
    errors: List[str]
    warnings: List[str]


class PluginValidator:
    """Validator for checking compiler plugin integrity and API compliance."""

    def __init__(self, min_compiler_version: str = "1.0.0"):
        self.min_compiler_version = min_compiler_version

    def validate_plugin(self, plugin: CompilerPlugin) -> ValidationResult:
        """Validate a plugin instance."""
        errors = []
        warnings = []
        
        if not hasattr(plugin, "config") or plugin.config is None:
            errors.append("Plugin missing required 'config' attribute")
        else:
            if not plugin.config.name:
                errors.append("Plugin config missing name")
        
        if not hasattr(plugin, "initialize"):
            errors.append("Plugin missing 'initialize' method")
            
        if not hasattr(plugin, "execute"):
            errors.append("Plugin missing 'execute' method")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            plugin_name=getattr(plugin.config, "name", "unknown") if hasattr(plugin, "config") else "unknown",
            errors=errors,
            warnings=warnings
        )


def create_plugin_validator(min_compiler_version: str = "1.0.0") -> PluginValidator:
    """Factory function for PluginValidator."""
    return PluginValidator(min_compiler_version=min_compiler_version)


@contextmanager
def validation_context(min_compiler_version: str = "1.0.0"):
    """Context manager for plugin validation operations."""
    validator = create_plugin_validator(min_compiler_version)
    try:
        yield validator
    finally:
        pass
