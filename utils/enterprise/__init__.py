"""
Enterprise Utilities Module

Enterprise-grade utilities for authentication, caching, monitoring,
metrics, cloud integration, and TruthGPT adapters.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'EnterpriseAuth',
    'EnterpriseCache',
    'EnterpriseMonitor',
    'EnterpriseMetrics',
    'EnterpriseCloudIntegration',
    'EnterpriseTruthGPTAdapter',
    'list_available_enterprise_components',
    'get_enterprise_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'EnterpriseAuth': '.auth',
    'EnterpriseCache': '.cache',
    'EnterpriseMonitor': '.monitor',
    'EnterpriseMetrics': '.metrics',
    'EnterpriseCloudIntegration': '.cloud_integration',
    'EnterpriseTruthGPTAdapter': '.truthgpt_adapter',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_enterprise_components() -> List[str]:
    """List all available enterprise utility components."""
    return _loader.list_components()


def get_enterprise_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about an enterprise component."""
    return _loader.get_component_info(component_name)
