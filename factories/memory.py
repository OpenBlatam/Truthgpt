"""
Memory Manager Factories
========================
Factory functions and registry for advanced memory managers.
"""
from typing import Any

from .registry import Registry

try:
    from optimization_core.modules.memory.advanced_memory_manager import (
        create_advanced_memory_manager,
        create_memory_config,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from ..modules.memory.advanced_memory_manager import (
            create_advanced_memory_manager,
            create_memory_config,
        )
    except (ImportError, ModuleNotFoundError):
        from modules.memory.advanced_memory_manager import (
            create_advanced_memory_manager,
            create_memory_config,
        )

MEMORY_MANAGERS = Registry(name="MemoryRegistry")


@MEMORY_MANAGERS.register("adaptive")
def build_adaptive(**kwargs: Any) -> Any:
    """Build an adaptive memory manager with dynamic offloading."""
    cfg = create_memory_config(**kwargs)
    return create_advanced_memory_manager(cfg)


@MEMORY_MANAGERS.register("static")
def build_static(**kwargs: Any) -> Any:
    """Build a static memory manager with conservative defaults."""
    kwargs.setdefault("use_xformers", False)
    kwargs.setdefault("prefer_bf16", False)
    cfg = create_memory_config(**kwargs)
    return create_advanced_memory_manager(cfg)






