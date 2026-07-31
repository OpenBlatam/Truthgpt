import sys
from typing import Dict, Any, List, Callable

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["registries.dataset_registry"] = _mod
    sys.modules["optimization_core.registries.dataset_registry"] = _mod

try:
    from data.registry import (
        register_dataset,
        build_dataset,
        _DATASET_BUILDERS as DATASET_BUILDERS,
    )
except (ImportError, ValueError):
    try:
        from optimization_core.data.registry import (
            register_dataset,
            build_dataset,
            _DATASET_BUILDERS as DATASET_BUILDERS,
        )
    except ImportError:
        from ..data.registry import (
            register_dataset,
            build_dataset,
            _DATASET_BUILDERS as DATASET_BUILDERS,
        )


class DatasetRegistry:
    """Wrapper class providing static methods for dataset creation and lookup."""

    @staticmethod
    def register(name: str) -> Callable:
        """Register a dataset builder function."""
        return register_dataset(name)

    @staticmethod
    def build(name: str, cfg: Dict[str, Any]) -> Any:
        """Build a dataset instance by registered name and config."""
        return build_dataset(name, cfg)

    @staticmethod
    def list_available() -> List[str]:
        """List names of all registered dataset builders."""
        return list(DATASET_BUILDERS.keys())


__all__ = ["DatasetRegistry", "register_dataset", "build_dataset", "DATASET_BUILDERS"]
