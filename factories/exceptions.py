"""
Factory System Exceptions
=========================
Comprehensive hierarchy of custom exceptions for registry lookups, object instantiation,
parameter validation, dependency resolution, hardware constraint assertions, lifecycle scopes,
plugin loading, and alias conflicts.
"""

import time
from typing import Any, Dict, List, Optional, Sequence


class RegistryError(Exception):
    """
    Base exception for all factory registry and instantiation errors.

    Attributes:
        message: Detailed exception description.
        registry_name: Optional identifier of the originating registry.
        error_code: Standardized error code string.
        timestamp: POSIX timestamp when exception was constructed.
        context: Optional dictionary containing additional diagnostic context.
    """

    def __init__(
        self,
        message: str,
        registry_name: Optional[str] = None,
        error_code: str = "ERR_REGISTRY_GENERIC",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.registry_name = registry_name
        self.error_code = error_code
        self.timestamp = time.time()
        self.context = context or {}
        super().__init__(self._formatted_message())

    def _formatted_message(self) -> str:
        prefix = f"[{self.registry_name}] " if self.registry_name else ""
        return f"{prefix}{self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Return structured dictionary representation of exception."""
        return {
            "error_code": self.error_code,
            "registry_name": self.registry_name,
            "message": self.message,
            "timestamp": self.timestamp,
            "context": self.context,
        }


# Alias for backward compatibility
FactoryError = RegistryError


class KeyNotFoundError(RegistryError, KeyError):
    """
    Raised when a requested key or alias is not found in a registry.

    Attributes:
        key: The key that was requested.
        available_keys: Sequence of valid keys present in the registry.
        suggestions: Close match suggestions (fuzzy matching).
    """

    def __init__(
        self,
        key: str,
        registry_name: Optional[str] = None,
        available_keys: Optional[Sequence[str]] = None,
        suggestions: Optional[Sequence[str]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.key = key
        self.available_keys = list(available_keys or [])
        self.suggestions = list(suggestions or [])

        if message is None:
            avail_str = (
                f" Available keys: {', '.join(self.available_keys)}."
                if self.available_keys
                else ""
            )
            sug_str = (
                f" Did you mean: {', '.join(self.suggestions)}?"
                if self.suggestions
                else ""
            )
            msg = f"Key '{key}' not found in registry.{avail_str}{sug_str}"
        else:
            msg = message

        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_KEY_NOT_FOUND",
            context={"requested_key": key, "suggestions": self.suggestions},
        )


class UnregisteredComponentError(KeyNotFoundError):
    """Raised when attempting to access or instantiate an unregistered component."""

    pass


class DuplicateRegistrationError(RegistryError, ValueError):
    """
    Raised when attempting to register an item under an existing key when override is disabled.

    Attributes:
        key: The duplicate key being registered.
        existing_target: Representation of the target currently registered under the key.
    """

    def __init__(
        self,
        key: str,
        registry_name: Optional[str] = None,
        existing_target: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.key = key
        self.existing_target = existing_target

        if message is None:
            target_str = (
                f" (currently pointing to '{existing_target}')"
                if existing_target
                else ""
            )
            msg = f"Item '{key}' is already registered in registry{target_str} and allow_override is False."
        else:
            msg = message

        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_DUPLICATE_REGISTRATION",
            context={"key": key, "existing_target": str(existing_target)},
        )


class DuplicateAliasError(DuplicateRegistrationError):
    """Raised when attempting to register an alias that collides with an existing canonical key or alias."""

    pass


class TypeMismatchError(RegistryError, TypeError):
    """
    Raised when a registered or instantiated object fails protocol or type constraints.

    Attributes:
        expected_type: Description of expected type/protocol.
        actual_type: Actual type received.
    """

    def __init__(
        self,
        expected_type: str,
        actual_type: str,
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.expected_type = expected_type
        self.actual_type = actual_type

        msg = (
            message
            or f"Expected object of type/protocol '{expected_type}', got '{actual_type}'."
        )
        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_TYPE_MISMATCH",
            context={"expected_type": expected_type, "actual_type": actual_type},
        )


class BuildError(RegistryError, RuntimeError):
    """
    Raised when an object builder, class instantiation, or factory construction fails.

    Attributes:
        key: Registry key being built.
        cause: Underlying exception that caused the failure.
    """

    def __init__(
        self,
        key: str,
        cause: Optional[Exception] = None,
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.key = key
        self.cause = cause

        if message is None:
            cause_str = f": {cause}" if cause else ""
            msg = f"Failed to build component '{key}'{cause_str}"
        else:
            msg = message

        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_BUILD_FAILED",
            context={"key": key, "cause": str(cause) if cause else None},
        )


class FactoryConfigurationError(RegistryError, ValueError):
    """
    Raised when invalid arguments or configuration dictionaries are passed to a factory manager.

    Attributes:
        invalid_keys: List of invalid or unknown configuration keys.
        missing_keys: List of required configuration keys that were missing.
    """

    def __init__(
        self,
        invalid_keys: Optional[List[str]] = None,
        missing_keys: Optional[List[str]] = None,
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.invalid_keys = invalid_keys or []
        self.missing_keys = missing_keys or []

        if message is None:
            details = []
            if self.missing_keys:
                details.append(
                    f"Missing required parameters: {', '.join(self.missing_keys)}"
                )
            if self.invalid_keys:
                details.append(
                    f"Invalid parameters: {', '.join(self.invalid_keys)}"
                )
            msg = (
                f"Configuration error: {'; '.join(details)}"
                if details
                else "Invalid factory configuration."
            )
        else:
            msg = message

        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_FACTORY_CONFIGURATION",
            context={
                "invalid_keys": self.invalid_keys,
                "missing_keys": self.missing_keys,
            },
        )


class ConfigurationValidationError(FactoryConfigurationError):
    """Raised when configuration validation fails schema or bound constraints."""

    pass


class HardwareConstraintError(RegistryError, RuntimeError):
    """
    Raised when host system hardware requirements (e.g. CUDA, BF16, Triton) are unsatisfied.

    Attributes:
        required_capability: Hardware feature required by the builder.
    """

    def __init__(
        self,
        required_capability: str,
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.required_capability = required_capability
        msg = (
            message
            or f"Hardware requirement '{required_capability}' is unsatisfied on current host system."
        )
        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_HARDWARE_CONSTRAINT",
            context={"required_capability": required_capability},
        )


class HardwareRequirementError(HardwareConstraintError):
    """Alias for HardwareConstraintError."""

    pass


class DependencyResolutionError(RegistryError, RuntimeError):
    """
    Raised when cyclic or unresolvable dependencies prevent component instantiation.
    """

    def __init__(
        self,
        dependency_chain: List[str],
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        msg = message or f"Unresolvable dependency chain detected: {chain_str}"
        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_DEPENDENCY_RESOLUTION",
            context={"dependency_chain": dependency_chain},
        )


class ScopeLifecycleError(RegistryError, RuntimeError):
    """
    Raised when an action violates the declared FactoryScope lifecycle manager.
    """

    def __init__(
        self,
        scope: str,
        reason: str,
        registry_name: Optional[str] = None,
    ) -> None:
        self.scope = scope
        self.reason = reason
        super().__init__(
            f"Scope lifecycle error for scope '{scope}': {reason}",
            registry_name=registry_name,
            error_code="ERR_SCOPE_LIFECYCLE",
            context={"scope": scope, "reason": reason},
        )


class InvalidScopeError(ScopeLifecycleError):
    """Raised when an invalid scope strategy is requested."""

    pass


class PluginLoadError(RegistryError, ImportError):
    """Raised when dynamically loading a plugin package fails."""

    def __init__(
        self,
        plugin_name: str,
        registry_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.plugin_name = plugin_name
        msg = message or f"Failed to load plugin package '{plugin_name}'."
        super().__init__(
            msg,
            registry_name=registry_name,
            error_code="ERR_PLUGIN_LOAD",
            context={"plugin_name": plugin_name},
        )


class PluginDependencyError(PluginLoadError):
    """Raised when a plugin fails due to missing external dependencies."""

    pass


class CircularDependencyError(DependencyResolutionError):
    """Raised when a cyclic dependency loop is detected during topological resolution."""

    pass


class ScopeContextExpiredError(ScopeLifecycleError):
    """Raised when accessing a contextual managed instance outside its active context."""

    def __init__(self, key: str, registry_name: Optional[str] = None) -> None:
        super().__init__(
            scope="contextual",
            reason=f"Contextual instance for '{key}' has expired or exited context manager.",
            registry_name=registry_name,
        )


class PluginValidationError(PluginLoadError):
    """Raised when a plugin fails structural interface validation."""

    pass


class TelemetryError(RegistryError, RuntimeError):
    """Raised when telemetry metric collection or profiling fails."""

    def __init__(self, message: str, registry_name: Optional[str] = None) -> None:
        super().__init__(
            message,
            registry_name=registry_name,
            error_code="ERR_TELEMETRY_FAILED",
        )


__all__ = [
    "RegistryError",
    "FactoryError",
    "KeyNotFoundError",
    "UnregisteredComponentError",
    "DuplicateRegistrationError",
    "DuplicateAliasError",
    "TypeMismatchError",
    "BuildError",
    "FactoryConfigurationError",
    "ConfigurationValidationError",
    "HardwareConstraintError",
    "HardwareRequirementError",
    "DependencyResolutionError",
    "CircularDependencyError",
    "ScopeLifecycleError",
    "InvalidScopeError",
    "ScopeContextExpiredError",
    "PluginLoadError",
    "PluginDependencyError",
    "PluginValidationError",
    "TelemetryError",
]
