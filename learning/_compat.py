"""
Dual-Namespace Compatibility Utility for Learning Subsystem.

Centralizes the sys.modules registration shim that was previously
duplicated across interfaces.py, types.py, exceptions.py, etc.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Optional


def register_dual_namespace(module: Optional[ModuleType] = None, module_name: Optional[str] = None) -> None:
    """
    Register a module under both 'optimization_core.learning.X' and 'learning.X' namespaces.
    
    This enables imports from either namespace to resolve to the same module object,
    supporting backward compatibility for code that uses the shorter 'learning.X' path.
    
    Args:
        module: The module object to register. If None, looks up by module_name.
        module_name: The __name__ of the module. If None, uses module.__name__.
    """
    if module is None and module_name is None:
        return
    
    name = module_name or (module.__name__ if module else None)
    if name is None:
        return
    
    mod = module or sys.modules.get(name)
    if mod is None:
        return
    
    if name.startswith("optimization_core.learning."):
        alt_name = "learning." + name[len("optimization_core.learning."):]
        sys.modules.setdefault(alt_name, mod)
    elif name.startswith("learning."):
        alt_name = "optimization_core.learning." + name[len("learning."):]
        sys.modules.setdefault(alt_name, mod)


def register_current_module() -> None:
    """Convenience function to register the calling module's dual namespace."""
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_name = frame.f_back.f_globals.get("__name__")
        if caller_name:
            register_dual_namespace(module_name=caller_name)
