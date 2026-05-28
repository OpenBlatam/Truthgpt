"""
Enterprise Utilities Module

This module contains enterprise-grade utilities for authentication, caching,
monitoring, and cloud integration.
"""

from __future__ import annotations

__all__ = [
    'EnterpriseAuth',
    'EnterpriseCache',
    'EnterpriseMonitor',
    'EnterpriseMetrics',
    'EnterpriseCloudIntegration',
    'EnterpriseTruthGPTAdapter',
]

_LAZY_IMPORTS = {
    'EnterpriseAuth': '..enterprise_auth',
    'EnterpriseCache': '..enterprise_cache',
    'EnterpriseMonitor': '..enterprise_monitor',
    'EnterpriseMetrics': '..enterprise_metrics',
    'EnterpriseCloudIntegration': '..enterprise_cloud_integration',
    'EnterpriseTruthGPTAdapter': '..enterprise_truthgpt_adapter',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for enterprise utility modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    import importlib
    module_path = _LAZY_IMPORTS[name]
    try:
        if module_path.startswith('..'):
            module = importlib.import_module(module_path, package=__name__)
        elif module_path.startswith('.'):
            module = importlib.import_module(module_path, package=__name__)
        else:
            module = importlib.import_module(module_path)
        
        if hasattr(module, name):
            obj = getattr(module, name)
        else:
            obj = module
        _import_cache[name] = obj
        return obj
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


