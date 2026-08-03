"""
Node Communicator and Worker Node Representation for Distributed Compilation
"""

import time
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class WorkerNode:
    """Worker node representation in a distributed compiler cluster."""

    def __init__(self, node_id: str, address: str, port: int, capabilities: Dict[str, Any]):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.capabilities = capabilities
        self.status = "idle"
        self.load = 0.0
        self.memory_usage = 0.0
        self.cpu_usage = 0.0
        self.gpu_usage = 0.0
        self.last_heartbeat = time.time()
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.performance_metrics = defaultdict(list)

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update worker performance and resource metrics."""
        self.load = metrics.get("load", 0.0)
        self.memory_usage = metrics.get("memory_usage", 0.0)
        self.cpu_usage = metrics.get("cpu_usage", 0.0)
        self.gpu_usage = metrics.get("gpu_usage", 0.0)
        self.last_heartbeat = time.time()

        for key, value in metrics.items():
            self.performance_metrics[key].append(value)

    def is_healthy(self, timeout_seconds: float = 30.0) -> bool:
        """Check if worker heartbeat is within acceptable time window."""
        return (time.time() - self.last_heartbeat) < timeout_seconds

    def get_utilization(self) -> float:
        """Get composite utilization across load, memory, cpu, and gpu."""
        return (self.load + self.memory_usage + self.cpu_usage + self.gpu_usage) / 4.0
