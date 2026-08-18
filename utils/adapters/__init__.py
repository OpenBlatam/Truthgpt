"""
Adapters Module

TruthGPT adapters, integration utilities, and enterprise connectors.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'TruthGPTAdapters',
    'TruthGPTAdapter',
    'TruthGPTIntegration',
    'TruthGPTEnhancedUtils',
    'TruthGPTCore',
    'EnterpriseTruthGPTAdapter',
    'list_available_adapter_components',
    'get_adapter_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'TruthGPTAdapters': '..enterprise_truthgpt_adapter',
    'TruthGPTAdapter': '..adapters.truthgpt_adapters',
    'TruthGPTIntegration': '..truthgpt_integration',
    'TruthGPTEnhancedUtils': '..truthgpt_enhanced_utils',
    'TruthGPTCore': '..truthgpt_core',
    'EnterpriseTruthGPTAdapter': '..enterprise_truthgpt_adapter',
}

_ALIASES: Dict[str, str] = {
    'TruthGPTAdapters': 'EnterpriseTruthGPTAdapter',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    aliases=_ALIASES,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_adapter_components() -> List[str]:
    """List all available adapter components."""
    return _loader.list_components()


def get_adapter_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about an adapter component."""
    return _loader.get_component_info(component_name)
