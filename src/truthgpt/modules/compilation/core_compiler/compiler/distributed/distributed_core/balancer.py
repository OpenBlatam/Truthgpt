import random
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from .base import LoadBalancingStrategy
from .nodes import WorkerNode

logger = logging.getLogger(__name__)

class LoadBalancer:
    """Advanced load balancer for distributed compilation"""
    
    def __init__(self, strategy: LoadBalancingStrategy, workers: List[WorkerNode]):
        self.strategy = strategy
        self.workers = workers
        self.current_worker = 0
        self.worker_weights = {worker.node_id: 1.0 for worker in workers}
        self.worker_performance = {worker.node_id: 1.0 for worker in workers}
        self.load_balancing_history = []
    
    def select_worker(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        """Select best worker for task"""
        try:
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_selection()
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_selection()
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection()
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_selection()
            elif self.strategy == LoadBalancingStrategy.RESOURCE_BASED:
                return self._resource_based_selection(task_requirements)
            elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
                return self._adaptive_selection(task_requirements)
            else:
                return self._default_selection()
        except Exception as e:
            logger.error(f"Worker selection failed: {e}")
            return None
    
    def _round_robin_selection(self) -> Optional[WorkerNode]:
        if not self.workers: return None
        worker = self.workers[self.current_worker]
        self.current_worker = (self.current_worker + 1) % len(self.workers)
        return worker
    
    def _least_connections_selection(self) -> Optional[WorkerNode]:
        if not self.workers: return None
        return min(self.workers, key=lambda w: w.active_tasks)
    
    def _weighted_round_robin_selection(self) -> Optional[WorkerNode]:
        if not self.workers: return None
        total_weight = sum(self.worker_weights.values())
        if total_weight == 0: return self._round_robin_selection()
        random_value = random.uniform(0, total_weight)
        current_weight = 0.0
        for worker in self.workers:
            current_weight += self.worker_weights[worker.node_id]
            if random_value <= current_weight: return worker
        return self.workers[-1]
    
    def _least_response_time_selection(self) -> Optional[WorkerNode]:
        if not self.workers: return None
        return min(self.workers, key=lambda w: w.performance_metrics.get("response_time", [0])[-1] if w.performance_metrics.get("response_time") else 0)
    
    def _resource_based_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        if not self.workers: return None
        suitable_workers = [w for w in self.workers if self._worker_meets_requirements(w, task_requirements)]
        if not suitable_workers: return None
        return min(suitable_workers, key=lambda w: w.get_utilization())
    
    def _adaptive_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        if not self.workers: return None
        candidates = [w for w in self.workers if self._worker_meets_requirements(w, task_requirements)]
        if not candidates: return self._round_robin_selection()
        return min(candidates, key=lambda w: w.get_utilization())
    
    def _default_selection(self) -> Optional[WorkerNode]:
        return self._round_robin_selection()
    
    def _worker_meets_requirements(self, worker: WorkerNode, requirements: Dict[str, Any]) -> bool:
        if "memory" in requirements and worker.memory_usage + requirements["memory"] > worker.capabilities.get("max_memory", 4096): return False
        if "cpu" in requirements and worker.cpu_usage + requirements["cpu"] > worker.capabilities.get("max_cpu", 1.0): return False
        if "gpu" in requirements and worker.gpu_usage + requirements["gpu"] > worker.capabilities.get("max_gpu", 1): return False
        return True
    
    
    def update_worker_performance(self, worker_id: str, performance: float):
        self.worker_performance[worker_id] = performance
    
    def get_load_balancing_metrics(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "total_workers": len(self.workers),
            "active_workers": len([w for w in self.workers if w.status == "active"]),
            "average_utilization": np.mean([w.get_utilization() for w in self.workers]) if self.workers else 0,
            "load_balance": 1.0 - (np.std([w.get_utilization() for w in self.workers]) if self.workers else 0)
        }
