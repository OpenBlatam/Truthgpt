"""
🖥️ TruthGPT Cloud - Host & Node System Telemetry
Collects real-time hardware metrics (CPU, RAM, Disk, Process threads, File Descriptors)
using psutil, with Prometheus gauge exposition and in-process fallback.
"""

import os
import time
from typing import Dict, Any

_HAS_PSUTIL = False
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# Prometheus Gauges for System Resources
PROM_NODE_CPU_PERCENT = None
PROM_NODE_MEMORY_BYTES = None
PROM_NODE_MEMORY_PERCENT = None
PROM_PROCESS_THREADS = None

try:
    from prometheus_client import Gauge
    from .prometheus import get_prometheus_registry

    _reg = get_prometheus_registry()
    PROM_NODE_CPU_PERCENT = Gauge(
        "truthgpt_node_cpu_utilization_percent",
        "Overall node CPU utilization percentage",
        registry=_reg,
    )
    PROM_NODE_MEMORY_BYTES = Gauge(
        "truthgpt_node_memory_used_bytes",
        "Physical memory used in bytes on the node",
        registry=_reg,
    )
    PROM_NODE_MEMORY_PERCENT = Gauge(
        "truthgpt_node_memory_utilization_percent",
        "Physical memory utilization percentage on the node",
        registry=_reg,
    )
    PROM_PROCESS_THREADS = Gauge(
        "truthgpt_process_threads_count",
        "Active OS threads in the TruthGPT Cloud worker process",
        registry=_reg,
    )
except Exception:
    pass


def get_system_metrics() -> Dict[str, Any]:
    """
    Collect comprehensive real-time system and process telemetry metrics.
    If psutil is unavailable, returns a safe simulated telemetry structure.
    """
    if not _HAS_PSUTIL:
        return {
            "has_psutil": False,
            "timestamp": time.time(),
            "cpu": {
                "percent": 0.0,
                "logical_cores": os.cpu_count() or 1,
                "physical_cores": os.cpu_count() or 1,
            },
            "memory": {
                "total_bytes": 0,
                "used_bytes": 0,
                "available_bytes": 0,
                "percent": 0.0,
                "total_mb": 0.0,
                "used_mb": 0.0,
            },
            "disk": {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent": 0.0,
            },
            "process": {
                "pid": os.getpid(),
                "memory_rss_bytes": 0,
                "threads_count": 1,
                "cpu_percent": 0.0,
            },
        }

    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_logical = psutil.cpu_count(logical=True) or 1
        cpu_physical = psutil.cpu_count(logical=False) or cpu_logical

        # Virtual Memory
        mem = psutil.virtual_memory()
        mem_total = mem.total
        mem_used = mem.used
        mem_avail = mem.available
        mem_pct = mem.percent

        # Disk Root
        try:
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            disk_total = disk.total
            disk_used = disk.used
            disk_free = disk.free
            disk_pct = disk.percent
        except Exception:
            disk_total, disk_used, disk_free, disk_pct = 0, 0, 0, 0.0

        # Process Metrics
        proc = psutil.Process(os.getpid())
        p_mem = proc.memory_info().rss
        p_threads = proc.num_threads()
        p_cpu = proc.cpu_percent(interval=None)
        try:
            p_files = len(proc.open_files())
        except Exception:
            p_files = 0

        res = {
            "has_psutil": True,
            "timestamp": time.time(),
            "cpu": {
                "percent": round(cpu_percent, 2),
                "logical_cores": cpu_logical,
                "physical_cores": cpu_physical,
            },
            "memory": {
                "total_bytes": mem_total,
                "used_bytes": mem_used,
                "available_bytes": mem_avail,
                "percent": round(mem_pct, 2),
                "total_mb": round(mem_total / (1024 * 1024), 2),
                "used_mb": round(mem_used / (1024 * 1024), 2),
            },
            "disk": {
                "total_bytes": disk_total,
                "used_bytes": disk_used,
                "free_bytes": disk_free,
                "percent": round(disk_pct, 2),
            },
            "process": {
                "pid": proc.pid,
                "memory_rss_bytes": p_mem,
                "memory_rss_mb": round(p_mem / (1024 * 1024), 2),
                "threads_count": p_threads,
                "cpu_percent": round(p_cpu, 2),
                "open_files_count": p_files,
            },
        }

        # Update Prometheus Gauges if active
        _update_system_prometheus(res)
        return res

    except Exception as e:
        return {
            "has_psutil": True,
            "error": str(e),
            "timestamp": time.time(),
            "cpu": {"percent": 0.0, "logical_cores": os.cpu_count() or 1},
            "memory": {"percent": 0.0, "total_mb": 0.0, "used_mb": 0.0},
        }


def _update_system_prometheus(metrics: Dict[str, Any]) -> None:
    """Publish current node system stats to Prometheus gauges."""
    if PROM_NODE_CPU_PERCENT is not None and "cpu" in metrics:
        try:
            PROM_NODE_CPU_PERCENT.set(metrics["cpu"]["percent"])
        except Exception:
            pass

    if PROM_NODE_MEMORY_BYTES is not None and "memory" in metrics:
        try:
            PROM_NODE_MEMORY_BYTES.set(metrics["memory"]["used_bytes"])
        except Exception:
            pass

    if PROM_NODE_MEMORY_PERCENT is not None and "memory" in metrics:
        try:
            PROM_NODE_MEMORY_PERCENT.set(metrics["memory"]["percent"])
        except Exception:
            pass

    if PROM_PROCESS_THREADS is not None and "process" in metrics:
        try:
            PROM_PROCESS_THREADS.set(metrics["process"]["threads_count"])
        except Exception:
            pass


__all__ = [
    "get_system_metrics",
    "_HAS_PSUTIL",
    "PROM_NODE_CPU_PERCENT",
    "PROM_NODE_MEMORY_BYTES",
    "PROM_NODE_MEMORY_PERCENT",
    "PROM_PROCESS_THREADS",
]
