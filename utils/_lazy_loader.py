"""
Shared lazy-import infrastructure for utils subpackages.

Eliminates the ~80 LOC boilerplate duplicated across all subpackage __init__.py
files by providing a reusable LazySubpackage descriptor and helper functions.

Usage in a subpackage __init__.py:

    from .._lazy_loader import create_lazy_module

    _LAZY_IMPORTS = {
        'MyClass': '.my_module',
    }
    _ALIASES = {
        'OldName': 'NewName',
    }

    _loader = create_lazy_module(
        package_name=__name__,
        lazy_imports=_LAZY_IMPORTS,
        aliases=_ALIASES,
        all_exports=[...],
    )
    __getattr__ = _loader.__getattr__
    __dir__ = _loader.__dir__
    list_components = _loader.list_components
    get_component_info = _loader.get_component_info
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional


class LazySubpackage:
    """
    Reusable lazy-import manager for subpackage modules.

    Provides:
    - __getattr__ with import caching & alias support
    - __dir__ for IDE discoverability
    - list_components() / get_component_info() discovery API
    """

    def __init__(
        self,
        package_name: str,
        lazy_imports: Dict[str, str],
        aliases: Optional[Dict[str, str]] = None,
        all_exports: Optional[List[str]] = None,
        globals_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            package_name: The __name__ of the subpackage (used for relative imports).
            lazy_imports: Mapping of symbol name -> relative module path.
            aliases: Optional mapping of symbol name -> actual attribute name in module.
            all_exports: Optional explicit __all__ list for the subpackage.
            globals_dict: The subpackage's globals() dict for __dir__ merging.
        """
        self._package_name = package_name
        self._lazy_imports = lazy_imports
        self._aliases = aliases or {}
        self._all_exports = all_exports or list(lazy_imports.keys())
        self._globals_dict = globals_dict or {}
        self._import_cache: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Lazy import system for subpackage modules."""
        if name.startswith('_'):
            raise AttributeError(f"module '{self._package_name}' has no attribute '{name}'")

        if name in self._import_cache:
            return self._import_cache[name]

        if name not in self._lazy_imports:
            raise AttributeError(f"module '{self._package_name}' has no attribute '{name}'")

        module_path = self._lazy_imports[name]
        target_attr = self._aliases.get(name, name)

        try:
            if module_path.startswith('.'):
                module = importlib.import_module(module_path, package=self._package_name)
            else:
                module = importlib.import_module(module_path)

            if hasattr(module, target_attr):
                obj = getattr(module, target_attr)
            elif hasattr(module, name):
                obj = getattr(module, name)
            else:
                obj = module

            self._import_cache[name] = obj
            return obj
        except (ImportError, AttributeError) as e:
            raise AttributeError(
                f"module '{self._package_name}' has no attribute '{name}'. Failed to import: {e}"
            ) from e

    def __dir__(self) -> List[str]:
        """Return all accessible symbols for IDE discoverability."""
        all_symbols = set(self._globals_dict.keys())
        all_symbols.update(self._lazy_imports.keys())
        all_symbols.update(self._all_exports)
        return sorted(all_symbols)

    def list_components(self) -> List[str]:
        """List all available components in this subpackage."""
        return list(self._lazy_imports.keys())

    def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get metadata information about a component."""
        if component_name not in self._lazy_imports:
            available = self.list_components()
            raise ValueError(
                f"Unknown component: {component_name}. Available: {available}"
            )

        return {
            'name': component_name,
            'module': self._lazy_imports[component_name],
            'package': self._package_name,
            'alias': self._aliases.get(component_name),
            'cached': component_name in self._import_cache,
        }


def create_lazy_module(
    package_name: str,
    lazy_imports: Dict[str, str],
    aliases: Optional[Dict[str, str]] = None,
    all_exports: Optional[List[str]] = None,
    globals_dict: Optional[Dict[str, Any]] = None,
) -> LazySubpackage:
    """
    Factory function to create a LazySubpackage instance.

    Returns a LazySubpackage whose __getattr__, __dir__, list_components, and
    get_component_info can be assigned directly to the subpackage module.
    """
    return LazySubpackage(
        package_name=package_name,
        lazy_imports=lazy_imports,
        aliases=aliases,
        all_exports=all_exports,
        globals_dict=globals_dict,
    )
