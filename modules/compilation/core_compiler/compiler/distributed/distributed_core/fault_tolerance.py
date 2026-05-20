import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from .base import DistributedCompilationConfig
from .nodes import WorkerNode

logger = logging.getLogger(__name__)

class FaultToleranceManager:
    """Fault tolerance manager for distributed compilation"""
    
    def __init__(self, config: DistributedCompilationConfig):
        self.config = config
        self.worker_health = {}
        self.fault_history = []
        self.recovery_actions = []
        self.checkpoint_data = {}
    
    def monitor_worker_health(self, workers: List[WorkerNode]) -> Dict[str, Any]:
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
        try:
            self.fault_history.append({"worker_id": worker.node_id, "fault_time": time.time(), "fault_type": "heartbeat_timeout", "recovery_action": "restart_worker"})
            self._attempt_worker_recovery(worker)
            logger.warning(f"Worker fault detected: {worker.node_id}")
        except Exception as e:
            logger.error(f"Worker fault handling failed: {e}")
    
    def _attempt_worker_recovery(self, worker: WorkerNode):
        try:
            worker.status = "recovering"
            self.recovery_actions.append({"worker_id": worker.node_id, "action": "restart", "timestamp": time.time()})
            logger.info(f"Attempting recovery for worker: {worker.node_id}")
        except Exception as e:
            logger.error(f"Worker recovery failed: {e}")
    
    def create_checkpoint(self, compilation_data: Dict[str, Any]) -> str:
        checkpoint_id = str(uuid.uuid4())
        self.checkpoint_data[checkpoint_id] = {"checkpoint_id": checkpoint_id, "timestamp": time.time(), "compilation_data": compilation_data, "worker_states": {}}
        logger.info(f"Checkpoint created: {checkpoint_id}")
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        if checkpoint_id in self.checkpoint_data:
            return self.checkpoint_data[checkpoint_id]["compilation_data"]
        return None
    
    def get_fault_tolerance_metrics(self) -> Dict[str, Any]:
        total_time = time.time() - (self.fault_history[0]["fault_time"] if self.fault_history else time.time())
        return {
            "total_faults": len(self.fault_history),
            "recovery_actions": len(self.recovery_actions),
            "checkpoints": len(self.checkpoint_data),
            "fault_rate": len(self.fault_history) / max(1, total_time),
            "recovery_success_rate": len([a for a in self.recovery_actions if a.get("success", False)]) / max(1, len(self.recovery_actions))
        }
