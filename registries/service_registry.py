import sys

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["registries.service_registry"] = _mod
    sys.modules["optimization_core.registries.service_registry"] = _mod

try:
    from core.service_registry import (
        ServiceRegistry,
        ServiceContainer,
        register_service,
        get_service,
    )
except (ImportError, ValueError):
    try:
        from optimization_core.core.service_registry import (
            ServiceRegistry,
            ServiceContainer,
            register_service,
            get_service,
        )
    except ImportError:
        from ..core.service_registry import (
            ServiceRegistry,
            ServiceContainer,
            register_service,
            get_service,
        )

__all__ = [
    "ServiceRegistry",
    "ServiceContainer",
    "register_service",
    "get_service",
]
