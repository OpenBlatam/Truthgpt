"""
Typed Exceptions Hierarchy for TruthGPT Interface Subsystem.
============================================================
"""
from __future__ import annotations

import sys
from typing import Any, Optional

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.exceptions":
        sys.modules["interface.exceptions"] = _mod
    elif __name__ == "interface.exceptions":
        sys.modules["optimization_core.interface.exceptions"] = _mod


class InterfaceError(Exception):
    """Base exception for all interface and user interaction errors."""

    def __init__(self, message: str, details: Optional[Any] = None, context: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.context = context or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


# ── Configuration Exceptions ──────────────────────────────────────

class ConfigError(InterfaceError):
    """Base exception for configuration and user preferences errors."""
    pass


ConfigurationError = ConfigError


class ConfigLoadError(ConfigError):
    """Raised when user preferences fail to load from disk."""
    pass


class ConfigSaveError(ConfigError):
    """Raised when user preferences cannot be persisted atomically."""
    pass


PreferencePersistenceError = ConfigSaveError


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail validation constraints."""
    pass


class CorruptedConfigError(ConfigError):
    """Raised when a config file contains invalid or corrupted JSON data."""
    pass


# ── Terminal & Console Exceptions ─────────────────────────────────

class TerminalError(InterfaceError):
    """Base exception for console and terminal handling errors."""
    pass


class QuickEditError(TerminalError):
    """Raised when Windows QuickEdit mode modification fails."""
    pass


class RenderingError(TerminalError):
    """Raised when terminal rendering or canvas layout fails."""
    pass


# ── Telemetry Exceptions ──────────────────────────────────────────

class TelemetryError(InterfaceError):
    """Base exception for system telemetry and monitoring errors."""
    pass


class BalanceFetchError(TelemetryError):
    """Raised when live API balance checks fail or time out."""
    pass


class MetricsCollectionError(TelemetryError):
    """Raised when CPU/memory system stats fail to collect."""
    pass


# ── TUI & Rendering Exceptions ────────────────────────────────────

class TUIError(InterfaceError):
    """Base exception for prompt_toolkit TUI rendering and execution errors."""
    pass


class TUIExecutionError(TUIError):
    """Raised when an interactive TUI session crashes during execution."""
    pass


class LayoutError(TUIError):
    """Raised when a layout container fails to build or render."""
    pass


LayoutRenderError = LayoutError


class KeybindingError(TUIError):
    """Raised when a keybinding definition or handler is invalid."""
    pass


class WidgetInitializationError(TUIError):
    """Raised when a prompt_toolkit widget or Rich control fails to initialize."""
    pass


# ── Menu & Navigation Exceptions ──────────────────────────────────

class MenuError(InterfaceError):
    """Base exception for menu routing and dispatch errors."""
    pass


class MenuNotFoundError(MenuError):
    """Raised when an unknown or unregistered menu name is requested."""
    pass


class InvalidMenuChoiceError(MenuError):
    """Raised when an invalid option or shortcut is selected in a menu."""
    pass


class MenuExecutionError(MenuError):
    """Raised when a menu handler encounters an unhandled exception during execution."""
    pass


MenuDispatchError = MenuExecutionError


class DuplicateMenuError(MenuError):
    """Raised when attempting to register a menu under an already existing ID without overwrite flag."""
    pass


# ── Theming Exceptions ────────────────────────────────────────────

class ThemeError(InterfaceError):
    """Base exception for visual theme and style resolution errors."""
    pass


class ThemeNotFoundError(ThemeError):
    """Raised when a requested theme name is not found in the ThemeRegistry."""
    pass


class InvalidThemeConfigurationError(ThemeError):
    """Raised when a theme palette contains malformed style specifications."""
    pass


# ── Input & Prompt Exceptions ─────────────────────────────────────

class InputError(InterfaceError):
    """Base exception for user input handling errors."""
    pass


class InputCancelledError(InputError):
    """Raised when a user cancels input or presses Ctrl+C / Escape."""
    pass


class InputTimeoutError(InputError):
    """Raised when user input exceeds the designated timeout."""
    pass


class InvalidInputFormatError(InputError):
    """Raised when user input fails validation format constraints."""
    pass


# ── Export & Persistence Exceptions ───────────────────────────────

class ExportError(InterfaceError):
    """Base exception for code extraction and report export errors."""
    pass


class CodeExtractionError(ExportError):
    """Raised when extracting markdown code blocks fails."""
    pass


# ── Swarm & History Exceptions ────────────────────────────────────

class SwarmInterfaceError(InterfaceError):
    """Raised when swarm interface components or missions fail."""
    pass


class HistoryLedgerError(InterfaceError):
    """Base exception for history logging and ledger persistence errors."""
    pass


class LedgerCorruptionError(HistoryLedgerError):
    """Raised when history database or JSON ledger is corrupted."""
    pass


__all__ = [
    "InterfaceError",
    "ConfigError",
    "ConfigurationError",
    "ConfigLoadError",
    "ConfigSaveError",
    "PreferencePersistenceError",
    "ConfigValidationError",
    "CorruptedConfigError",
    "TerminalError",
    "QuickEditError",
    "RenderingError",
    "TelemetryError",
    "BalanceFetchError",
    "MetricsCollectionError",
    "TUIError",
    "TUIExecutionError",
    "LayoutError",
    "LayoutRenderError",
    "KeybindingError",
    "WidgetInitializationError",
    "MenuError",
    "MenuNotFoundError",
    "InvalidMenuChoiceError",
    "MenuExecutionError",
    "MenuDispatchError",
    "DuplicateMenuError",
    "ThemeError",
    "ThemeNotFoundError",
    "InvalidThemeConfigurationError",
    "InputError",
    "InputCancelledError",
    "InputTimeoutError",
    "InvalidInputFormatError",
    "ExportError",
    "CodeExtractionError",
    "SwarmInterfaceError",
    "HistoryLedgerError",
    "LedgerCorruptionError",
]
