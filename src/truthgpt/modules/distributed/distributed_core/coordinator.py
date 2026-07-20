import asyncio
import logging
import time
import queue
import zmq
import redis
from typing import Dict, List, Any

from .base import DistributedConfig, WorkerInfo, TaskAssignment, CommunicationBackend
from .worker import DistributedWorker
from .balancer import LoadBalancer

class DistributedCoordinator:
    """Distributed coordinator for TruthGPT"""
    def __init__(self, config: DistributedConfig):
        self.config, self.logger = config, logging.getLogger(f"DistributedCoordinator_{id(self)}")
        self.workers, self.worker_info = {}, {}
        self.load_balancer = LoadBalancer(config)
        self.task_queue, self.completed_tasks, self.failed_tasks = queue.Queue(), [], []
        self.context, self.socket = None, None
        self._init_communication()
        self.coordinator_metrics = {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "average_execution_time": 0.0, "worker_utilization": {}}

    def _init_communication(self):
        if self.config.communication_backend == CommunicationBackend.ZMQ:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(f"tcp://*:{self.config.master_port}")
        elif self.config.communication_backend == CommunicationBackend.REDIS:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    async def start_coordinator(self):
        self.logger.info("Starting distributed coordinator")
        await asyncio.gather(self._worker_management_loop(), self._task_distribution_loop(), self._communication_loop(), self._monitoring_loop())

    async def _worker_management_loop(self):
        while True:
            try:
                await self._check_worker_health()
                if self.config.enable_auto_scaling: await self._auto_scaling()
            except Exception as e: self.logger.error(f"Worker management error: {e}")
            await asyncio.sleep(self.config.heartbeat_interval)

    async def _check_worker_health(self):
        now = time.time()
        unhealthy = [wid for wid, info in self.worker_info.items() if now - info.last_heartbeat > self.config.timeout]
        for wid in unhealthy:
            self.logger.warning(f"Worker {wid} unhealthy, removing")
            await self._remove_worker(wid)

    async def _auto_scaling(self):
        load = self._calculate_load()
        if load > self.config.scaling_threshold and len(self.workers) < self.config.max_workers: await self._scale_up()
        elif load < 0.3 and len(self.workers) > self.config.min_workers: await self._scale_down()

    def _calculate_load(self) -> float:
        if not self.workers: return 0.0
        avg_cpu = sum(w.resource_usage.get("cpu_percent", 0) for w in self.worker_info.values()) / len(self.worker_info)
        avg_mem = sum(w.resource_usage.get("memory_percent", 0) for w in self.worker_info.values()) / len(self.worker_info)
        return (avg_cpu + avg_mem) / 200.0

    async def _scale_up(self):
        wid = f"worker_{len(self.workers)}"
        worker = DistributedWorker(wid, self.config)
        self.workers[wid], self.worker_info[wid] = worker, worker.info
        self.load_balancer.add_worker(worker.info)

    async def _scale_down(self):
        if len(self.workers) > self.config.min_workers:
            wid = min(self.workers.keys(), key=lambda w: self.worker_info[w].tasks_completed)
            await self._remove_worker(wid)

    async def _remove_worker(self, wid: str):
        if wid in self.workers:
            del self.workers[wid]
            del self.worker_info[wid]
            self.load_balancer.remove_worker(wid)

    async def _task_distribution_loop(self):
        while True:
            try:
                if not self.task_queue.empty(): await self._distribute_task(self.task_queue.get())
                else: await asyncio.sleep(0.1)
            except Exception as e: self.logger.error(f"Task distribution error: {e}")

    async def _distribute_task(self, task: TaskAssignment):
        wid = self.load_balancer.select_worker(task.data)
        if wid and wid in self.workers:
            task.worker_id = wid
            self.workers[wid].assign_task(task)

    async def _communication_loop(self):
        while True:
            try: await asyncio.sleep(0.1)
            except Exception as e: self.logger.error(f"Communication error: {e}")

    async def _monitoring_loop(self):
        while True:
            try: await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e: self.logger.error(f"Monitoring error: {e}")
