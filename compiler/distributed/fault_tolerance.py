"""
Fault Tolerance Manager Module for Distributed Compilation
"""

import time
import uuid
import logging
from typing import Dict, List, Optional, Any

from .node_communicator import WorkerNode

logger = logging.getLogger(__name__)


class FaultToleranceManager:
    """Fault tolerance manager for monitoring workers, checkpoints, and recoveries."""

    def __init__(self, config: Any):
        self.config = config
        self.worker_health: Dict[str, Any] = {}
        self.fault_history: List[Dict[str, Any]] = []
        self.recovery_actions: List[Dict[str, Any]] = []
        self.checkpoint_data: Dict[str, Dict[str, Any]] = {}
        self.redundancy_manager = None

    def monitor_worker_health(self, workers: List[WorkerNode]) -> Dict[str, Any]:
        """Monitor health status of worker cluster."""
        try:
            health_status = {}

            for worker in workers:
                is_healthy = worker.is_healthy()
                health_status[worker.node_id] = {
                    "healthy": is_healthy,
                    "last_heartbeat": worker.last_heartbeat,
                    "response_time": time.time() - worker.last_heartbeat,
                    "load": worker.load,
                    "memory_usage": worker.memory_usage,
                    "cpu_usage": worker.cpu_usage
                }

                if not is_healthy:
                    self._handle_worker_fault(worker)

            return health_status

        except Exception as e:
            logger.error(f"Worker health monitoring failed: {e}")
            return {}

    def _handle_worker_fault(self, worker: WorkerNode):
        """Handle detected worker fault."""
        try:
            fault_info = {
                "worker_id": worker.node_id,
                "fault_time": time.time(),
                "fault_type": "heartbeat_timeout",
                "recovery_action": "restart_worker"
            }

            self.fault_history.append(fault_info)
            self._attempt_worker_recovery(worker)
            logger.warning(f"Worker fault detected: {worker.node_id}")

        except Exception as e:
            logger.error(f"Worker fault handling failed: {e}")

    def _attempt_worker_recovery(self, worker: WorkerNode):
        """Attempt to recover worker node."""
        try:
            worker.status = "recovering"
            recovery_action = {
                "worker_id": worker.node_id,
                "action": "restart",
                "timestamp": time.time(),
                "success": True
            }
            self.recovery_actions.append(recovery_action)
            logger.info(f"Attempting recovery for worker: {worker.node_id}")

        except Exception as e:
            logger.error(f"Worker recovery failed: {e}")

    def create_checkpoint(self, compilation_data: Dict[str, Any]) -> str:
        """Create compilation checkpoint."""
        try:
            checkpoint_id = str(uuid.uuid4())
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "timestamp": time.time(),
                "compilation_data": compilation_data,
                "worker_states": {}
            }

            self.checkpoint_data[checkpoint_id] = checkpoint_data
            logger.info(f"Checkpoint created: {checkpoint_id}")
            return checkpoint_id

        except Exception as e:
            logger.error(f"Checkpoint creation failed: {e}")
            return ""

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Restore compilation checkpoint."""
        try:
            if checkpoint_id in self.checkpoint_data:
                checkpoint = self.checkpoint_data[checkpoint_id]
                logger.info(f"Checkpoint restored: {checkpoint_id}")
                return checkpoint["compilation_data"]
            else:
                logger.warning(f"Checkpoint not found: {checkpoint_id}")
                return None

        except Exception as e:
            logger.error(f"Checkpoint restoration failed: {e}")
            return None

    def get_fault_tolerance_metrics(self) -> Dict[str, Any]:
        """Get fault tolerance metrics."""
        return {
            "total_faults": len(self.fault_history),
            "recovery_actions": len(self.recovery_actions),
            "checkpoints": len(self.checkpoint_data),
            "fault_rate": len(self.fault_history) / max(1, time.time() - (self.fault_history[0]["fault_time"] if self.fault_history else time.time())),
            "recovery_success_rate": len([a for a in self.recovery_actions if a.get("success", False)]) / max(1, len(self.recovery_actions))
        }
