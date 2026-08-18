"""
Metrics Utilities Package

Unified metrics utilities consolidating basic training metrics
and advanced metrics collection with statistical analysis.

Basic metrics (from .basic):
    - perplexity_from_loss() — compute perplexity from validation loss
    - tokens_per_second() — compute token throughput

Advanced metrics (from .advanced):
    - MetricValue — timestamped metric value
    - MetricStats — statistical summary
    - AdvancedMetricsCollector — full-featured metrics collector
    - create_metrics_collector() — factory function
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    # Basic
    'perplexity_from_loss',
    'tokens_per_second',
    # Advanced
    'MetricValue',
    'MetricStats',
    'AdvancedMetricsCollector',
    'create_metrics_collector',
    'list_available_metrics_components',
    'get_metrics_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'perplexity_from_loss': '.basic',
    'tokens_per_second': '.basic',
    'MetricValue': '.advanced',
    'MetricStats': '.advanced',
    'AdvancedMetricsCollector': '.advanced',
    'create_metrics_collector': '.advanced',
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


def list_available_metrics_components() -> List[str]:
    """List all available metrics components."""
    return _loader.list_components()


def get_metrics_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a metrics component."""
    return _loader.get_component_info(component_name)
