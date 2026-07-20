import logging
import random
import time
from typing import Dict, Any, Optional

from .base import DistributedConfig, WorkerInfo, WorkerStatus, LoadBalancingStrategy

class LoadBalancer:
    """Load balancer for distributed computing"""
    def __init__(self, config: DistributedConfig):
        self.config, self.logger = config, logging.getLogger(f"LoadBalancer_{id(self)}")
        self.workers, self.worker_weights = {}, {}
        self.round_robin_index, self.consistent_hash_ring = 0, {}
        self.load_balancing_metrics = {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "average_response_time": 0.0}

    def add_worker(self, worker_info: WorkerInfo):
        self.workers[worker_info.worker_id], self.worker_weights[worker_info.worker_id] = worker_info, 1.0
        if self.config.load_balancing_strategy == LoadBalancingStrategy.CONSISTENT_HASH: self._update_consistent_hash_ring()

    def remove_worker(self, worker_id: str):
        if worker_id in self.workers:
            del self.workers[worker_id]
            del self.worker_weights[worker_id]
            if self.config.load_balancing_strategy == LoadBalancingStrategy.CONSISTENT_HASH: self._update_consistent_hash_ring()

    def select_worker(self, task_data: Dict[str, Any] = None) -> Optional[str]:
        if not self.workers: return None
        available = {wid: w for wid, w in self.workers.items() if w.status == WorkerStatus.IDLE}
        if not available: return None
        strat = self.config.load_balancing_strategy
        if strat == LoadBalancingStrategy.ROUND_ROBIN: return self._round_robin(available)
        if strat == LoadBalancingStrategy.LEAST_CONNECTIONS: return min(available.keys(), key=lambda w: available[w].tasks_completed)
        if strat == LoadBalancingStrategy.LEAST_RESPONSE_TIME: return min(available.keys(), key=lambda w: available[w].average_response_time)
        if strat == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: return self._weighted_round_robin(available)
        if strat == LoadBalancingStrategy.CONSISTENT_HASH: return self._consistent_hash(available, task_data)
        return self._round_robin(available)

    def _round_robin(self, available):
        ids = list(available.keys())
        res = ids[self.round_robin_index % len(ids)]
        self.round_robin_index += 1
        return res

    def _weighted_round_robin(self, available):
        total = sum(self.worker_weights[w] for w in available.keys())
        if total == 0: return self._round_robin(available)
        rand, cur = random.uniform(0, total), 0
        for wid in available.keys():
            cur += self.worker_weights[wid]
            if rand <= cur: return wid
        return list(available.keys())[0]

    def _consistent_hash(self, available, data):
        if not self.consistent_hash_ring: return self._round_robin(available)
        h = hash(str(data)) if data else hash(time.time())
        sorted_keys = sorted(self.consistent_hash_ring.keys())
        for k in sorted_keys:
            if h <= k: return self.consistent_hash_ring[k]
        return self.consistent_hash_ring[sorted_keys[0]]

    def _update_consistent_hash_ring(self):
        self.consistent_hash_ring = {hash(f"{wid}_{i}"): wid for wid in self.workers.keys() for i in range(100)}

    def update_worker_performance(self, worker_id: str, data: Dict[str, Any]):
        if worker_id in self.workers:
            self.workers[worker_id].performance_metrics.update(data)
            self.worker_weights[worker_id] = data.get("success_rate", 1.0) / max(data.get("average_response_time", 1.0), 0.1)

    def get_load_balancing_stats(self) -> Dict[str, Any]:
        return {"strategy": self.config.load_balancing_strategy.value, "total_workers": len(self.workers), "available_workers": len([w for w in self.workers.values() if w.status == WorkerStatus.IDLE]), "worker_weights": self.worker_weights, "load_balancing_metrics": self.load_balancing_metrics}
