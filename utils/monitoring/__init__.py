"""
Monitoring Utilities Module

Real-time training telemetry, alerting, observability, and dashboard monitors.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'MonitorTraining',
    'RealTimePerformanceMonitor',
    'TruthGPTMonitoring',
    'VisualizeTraining',
    'visualize_checkpoints',
    'summarize_run',
    'CompareRuns',
    'compare_runs',
    'get_run_info',
    'ExperimentTracker',
    'MonitoringUtils',
    'Observability',
    'list_available_monitoring_components',
    'get_monitoring_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'MonitorTraining': '.monitor_training',
    'monitor_training': '.monitor_training',
    'RealTimePerformanceMonitor': '.realtime_monitor',
    'MonitoringUtils': '.monitoring_utils',
    'Observability': '.observability',
    # These still reference parent-level files that haven't been moved
    'TruthGPTMonitoring': '..truthgpt_monitoring',
    'VisualizeTraining': '..visualize_training',
    'visualize_checkpoints': '..visualize_training',
    'summarize_run': '..visualize_training',
    'CompareRuns': '..compare_runs',
    'compare_runs': '..compare_runs',
    'get_run_info': '..compare_runs',
    'ExperimentTracker': '..experiment_tracker',
}

_ALIASES: Dict[str, str] = {
    'MonitorTraining': 'get_gpu_stats',
    'VisualizeTraining': 'visualize_checkpoints',
    'CompareRuns': 'compare_runs',
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


def list_available_monitoring_components() -> List[str]:
    """List all available monitoring components."""
    return _loader.list_components()


def get_monitoring_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a monitoring component."""
    return _loader.get_component_info(component_name)
