"""
Load Balancer Module for Distributed Compilation
"""

import random
import logging
import numpy as np
from typing import Dict, List, Optional, Any

from .node_communicator import WorkerNode

logger = logging.getLogger(__name__)


class LoadBalancer:
    """Advanced load balancer for distributed compilation."""

    def __init__(self, strategy: Any, workers: List[WorkerNode]):
        self.strategy = strategy
        self.workers = workers
        self.current_worker = 0
        self.worker_weights = {worker.node_id: 1.0 for worker in workers}
        self.worker_performance = {worker.node_id: 1.0 for worker in workers}
        self.load_balancing_history = []

    def select_worker(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        """Select the optimal worker node for a task based on load balancing strategy."""
        try:
            from .distributed_compiler import LoadBalancingStrategy
            
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
            elif self.strategy == LoadBalancingStrategy.MACHINE_LEARNING:
                return self._machine_learning_selection(task_requirements)
            elif self.strategy == LoadBalancingStrategy.QUANTUM_OPTIMIZED:
                return self._quantum_optimized_selection(task_requirements)
            else:
                return self._round_robin_selection()
        except Exception as e:
            logger.error(f"Load balancing selection failed: {e}")
            return self.workers[0] if self.workers else None

    def _round_robin_selection(self) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        worker = self.workers[self.current_worker]
        self.current_worker = (self.current_worker + 1) % len(self.workers)
        return worker

    def _least_connections_selection(self) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        return min(self.workers, key=lambda w: w.active_tasks)

    def _weighted_round_robin_selection(self) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        weights = [self.worker_weights.get(w.node_id, 1.0) for w in self.workers]
        total_weight = sum(weights)
        if total_weight <= 0:
            return self._round_robin_selection()
        probabilities = [w / total_weight for w in weights]
        return random.choices(self.workers, weights=probabilities, k=1)[0]

    def _least_response_time_selection(self) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        return min(self.workers, key=lambda w: np.mean(w.performance_metrics.get("response_time", [1.0])))

    def _resource_based_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        return min(self.workers, key=lambda w: w.get_utilization())

    def _adaptive_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        if not self.workers:
            return None
        healthy_workers = [w for w in self.workers if w.is_healthy()]
        if not healthy_workers:
            healthy_workers = self.workers
        return min(healthy_workers, key=lambda w: (w.get_utilization() + w.active_tasks * 0.1))

    def _machine_learning_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        return self._adaptive_selection(task_requirements)

    def _quantum_optimized_selection(self, task_requirements: Dict[str, Any]) -> Optional[WorkerNode]:
        return self._adaptive_selection(task_requirements)

    def update_worker_performance(self, worker_id: str, execution_time: float, success: bool):
        """Update historical performance metrics for worker."""
        if worker_id in self.worker_performance:
            alpha = 0.1
            score = 1.0 / max(0.001, execution_time) if success else 0.1
            self.worker_performance[worker_id] = (1 - alpha) * self.worker_performance[worker_id] + alpha * score

    def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get summary load balancing metrics across all workers."""
        if not self.workers:
            return {}
        return {
            "total_workers": len(self.workers),
            "healthy_workers": len([w for w in self.workers if w.is_healthy()]),
            "average_utilization": float(np.mean([w.get_utilization() for w in self.workers])),
            "load_balance": float(1.0 - np.std([w.get_utilization() for w in self.workers]))
        }
