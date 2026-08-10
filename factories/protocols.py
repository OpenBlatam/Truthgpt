"""
Factory Protocols
=================
typing.Protocol interfaces defining standard structural contracts for builders,
async builders, configurable components, lifecycle management, factory dispatches,
validation, plugins, serialization, health checks, event notifications, dynamic scoping,
and hardware capability providers.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    runtime_checkable,
)

T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


@runtime_checkable
class BuilderProtocol(Protocol[T_co]):
    """Protocol for synchronous factory builder callables/classes."""

    def __call__(self, *args: Any, **kwargs: Any) -> T_co:
        ...


@runtime_checkable
class AsyncBuilderProtocol(Protocol[T_co]):
    """Protocol for asynchronous factory builder callables/coroutines."""

    async def __call__(self, *args: Any, **kwargs: Any) -> T_co:
        ...


@runtime_checkable
class ConfigurableProtocol(Protocol):
    """Protocol for objects that accept runtime configuration dictionaries."""

    def configure(self, config: Dict[str, Any]) -> None:
        ...


@runtime_checkable
class LifecycleProtocol(Protocol):
    """Protocol for objects supporting basic explicit lifecycle hooks."""

    def initialize(self) -> None:
        ...

    def shutdown(self) -> None:
        ...


@runtime_checkable
class ExtendedLifecycleProtocol(LifecycleProtocol, Protocol):
    """Protocol for objects supporting comprehensive lifecycle hooks including reset and validate."""

    def reset(self) -> None:
        ...

    def validate(self) -> bool:
        ...


@runtime_checkable
class FactoryProtocol(Protocol[T_co]):
    """Protocol for component factory managers."""

    def build(self, name: str, *args: Any, **kwargs: Any) -> T_co:
        ...


@runtime_checkable
class RegistryProtocol(Protocol[T_co]):
    """Protocol defining standard registry operations."""

    def register(self, name: Optional[str] = None, **kwargs: Any) -> Any:
        ...

    def get(self, name: str) -> T_co:
        ...

    def build(self, name: str, *args: Any, **kwargs: Any) -> Any:
        ...

    def keys(self) -> List[str]:
        ...

    def items(self) -> List[Tuple[str, T_co]]:
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for argument and configuration validators."""

    def validate(self, kwargs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        ...


@runtime_checkable
class ValidationResultProtocol(Protocol):
    """Protocol for structured validation results."""

    @property
    def is_valid(self) -> bool:
        ...

    @property
    def errors(self) -> List[str]:
        ...


@runtime_checkable
class SerializableProtocol(Protocol):
    """Protocol for factory components supporting dictionary serialization."""

    def to_dict(self) -> Dict[str, Any]:
        ...

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> Any:
        ...


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol for custom external factory plugins."""

    def register_components(self, registry: Any) -> None:
        ...


@runtime_checkable
class PluginLoaderProtocol(Protocol):
    """Protocol for dynamic plugin package discovery and registration."""

    def load_plugin(self, package_name: str) -> bool:
        ...


@runtime_checkable
class HealthCheckProtocol(Protocol):
    """Protocol for component health check assertions."""

    def health_check(self) -> Dict[str, Any]:
        ...


@runtime_checkable
class ComponentHealthProtocol(HealthCheckProtocol, Protocol):
    """Extended health check protocol returning status, status string, and diagnostic telemetry."""

    def get_health_status(self) -> Tuple[bool, str, Dict[str, Any]]:
        ...


@runtime_checkable
class RegistryEventProtocol(Protocol):
    """Protocol for registry lifecycle event listeners."""

    def on_event(self, event_type: str, name: str, payload: Any) -> None:
        ...


@runtime_checkable
class HookProtocol(Protocol):
    """Protocol for event lifecycle hook callables."""

    def __call__(self, name: str, item_or_exc: Any) -> None:
        ...


@runtime_checkable
class ScopeContextProtocol(Protocol):
    """Protocol for managing factory scoping contexts."""

    def enter_scope(self, scope_name: str) -> None:
        ...

    def exit_scope(self, scope_name: str) -> None:
        ...


@runtime_checkable
class HardwareAwareProtocol(Protocol):
    """Protocol for hardware capability-aware factory objects."""

    def is_hardware_supported(self) -> bool:
        ...

    def get_hardware_requirements(self) -> List[str]:
        ...


@runtime_checkable
class HardwareCapabilityProviderProtocol(Protocol):
    """Protocol for querying active host system hardware capabilities."""

    def detect_capabilities(self) -> Dict[str, Any]:
        ...


@runtime_checkable
class AsyncRegistryProtocol(Protocol[T_co]):
    """Protocol for registries supporting asynchronous component construction."""

    async def abuild(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Asynchronously build an object by name."""
        ...


@runtime_checkable
class TelemetryAwareProtocol(Protocol):
    """Protocol for factory registries or components exposing execution telemetry metrics."""

    def get_telemetry(self) -> Dict[str, Any]:
        """Return structured execution telemetry dictionary."""
        ...


TelemetryProtocol = TelemetryAwareProtocol


@runtime_checkable
class DependencyResolvableProtocol(Protocol):
    """Protocol for registries capable of topological dependency graph resolution."""

    def resolve_dependencies(self, name: str) -> List[str]:
        """Return topologically sorted sequence of dependency keys."""
        ...


@runtime_checkable
class PipelineStepProtocol(Protocol):
    """Protocol for components executing as a step in a composite pipeline."""

    def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step logic over pipeline context and return updated context."""
        ...


__all__ = [
    "BuilderProtocol",
    "AsyncBuilderProtocol",
    "ConfigurableProtocol",
    "LifecycleProtocol",
    "ExtendedLifecycleProtocol",
    "FactoryProtocol",
    "RegistryProtocol",
    "ValidatorProtocol",
    "ValidationResultProtocol",
    "SerializableProtocol",
    "PluginProtocol",
    "PluginLoaderProtocol",
    "HealthCheckProtocol",
    "ComponentHealthProtocol",
    "RegistryEventProtocol",
    "HookProtocol",
    "ScopeContextProtocol",
    "HardwareAwareProtocol",
    "HardwareCapabilityProviderProtocol",
    "AsyncRegistryProtocol",
    "TelemetryAwareProtocol",
    "DependencyResolvableProtocol",
    "PipelineStepProtocol",
]
