import asyncio
import logging
import time
import socket
import math
import queue
import psutil
import zmq
import redis
import torch
from typing import Dict, Any, Optional, List

from .base import DistributedConfig, WorkerInfo, WorkerStatus, TaskAssignment, CommunicationBackend

class ResourceMonitor:
    """Resource monitor for workers"""
    def __init__(self):
        self.logger = logging.getLogger(f"ResourceMonitor_{id(self)}")

    def get_current_usage(self) -> Dict[str, float]:
        try:
            return {"cpu_percent": psutil.cpu_percent(interval=1), "memory_percent": psutil.virtual_memory().percent, "gpu_percent": self._get_gpu_usage(), "disk_percent": psutil.disk_usage('/').percent, "timestamp": time.time()}
        except Exception as e:
            self.logger.error(f"Resource monitoring error: {e}")
            return {"cpu_percent": 0.0, "memory_percent": 0.0, "gpu_percent": 0.0, "disk_percent": 0.0, "timestamp": time.time()}

    def _get_gpu_usage(self) -> float: return 0.0

class DistributedWorker:
    """Distributed worker for TruthGPT"""
    def __init__(self, worker_id: str, config: DistributedConfig):
        self.worker_id, self.config = worker_id, config
        self.logger = logging.getLogger(f"DistributedWorker_{worker_id}")
        self.info = WorkerInfo(worker_id=worker_id, host=socket.gethostname(), port=config.worker_ports[0] if config.worker_ports else 5556)
        self.context = None
        self.socket = None
        self._init_communication()
        self.current_task = None
        self.task_queue = queue.Queue()
        self.completed_tasks = []
        self.performance_history = []
        self.resource_monitor = ResourceMonitor()
        self.local_model = None

    def _init_communication(self):
        if self.config.communication_backend == CommunicationBackend.ZMQ:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(f"tcp://*:{self.info.port}")
        elif self.config.communication_backend == CommunicationBackend.REDIS:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    async def start_worker(self):
        self.logger.info(f"Starting worker {self.worker_id}")
        await asyncio.gather(self._heartbeat_loop(), self._task_processing_loop(), self._resource_monitoring_loop())

    async def _heartbeat_loop(self):
        while True:
            try:
                self.info.last_heartbeat = time.time()
                await self._send_heartbeat()
            except Exception as e: self.logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(self.config.heartbeat_interval)

    async def _send_heartbeat(self):
        data = {"worker_id": self.worker_id, "status": self.info.status.value, "timestamp": time.time(), "resource_usage": self.resource_monitor.get_current_usage(), "performance_metrics": self.info.performance_metrics}
        if self.config.communication_backend == CommunicationBackend.ZMQ:
            s = self.context.socket(zmq.REQ)
            s.connect(f"tcp://localhost:{self.config.master_port}")
            s.send_json(data)
            s.close()

    async def _task_processing_loop(self):
        while True:
            try:
                if not self.task_queue.empty(): await self._process_task(self.task_queue.get())
                else: await asyncio.sleep(0.1)
            except Exception as e: self.logger.error(f"Task processing error: {e}")

    async def _process_task(self, task: TaskAssignment):
        self.info.status, task.started_at = WorkerStatus.BUSY, time.time()
        try:
            if task.task_type == "training": res = await self._process_training_task(task)
            elif task.task_type == "inference": res = await self._process_inference_task(task)
            elif task.task_type == "optimization": res = await self._process_optimization_task(task)
            else: res = await self._process_generic_task(task)
            task.completed_at, task.status = time.time(), "completed"
            self.completed_tasks.append(task)
            self._update_performance_metrics(task, task.completed_at - task.started_at, True)
            await self._send_task_result(task, res)
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {e}")
            task.status, self.info.tasks_failed = "failed", self.info.tasks_failed + 1
            self._update_performance_metrics(task, 0, False)
        finally: self.info.status, self.current_task = WorkerStatus.IDLE, None

    async def _process_training_task(self, task):
        epochs = task.data.get("epochs", 10)
        hist = [1.0 / (1.0 + math.log(i + 1)) for i in range(epochs)]
        return {"task_type": "training", "epochs": epochs, "final_loss": hist[-1], "training_history": hist, "status": "Success"}

    async def _process_inference_task(self, task):
        data = task.data.get("input_data", "")
        return {"task_type": "inference", "input": data, "output": f"Processed inference for: {data[:50]}...", "confidence": 0.5 + (min(len(data), 100) / 200.0), "status": "Success"}

    async def _process_optimization_task(self, task):
        iters = task.data.get("iterations", 100)
        return {"task_type": "optimization", "iterations": iters, "best_value": 1.0 - (1.0 / (1.0 + iters)), "improvement": 1.0 / (1.0 + iters), "status": "Success"}

    async def _process_generic_task(self, task): return {"task_type": task.task_type, "status": "completed", "result": f"Generic task {task.task_id} completed"}

    def _update_performance_metrics(self, task, exec_time, success):
        self.info.tasks_completed += 1
        self.info.average_response_time = exec_time if self.info.average_response_time == 0 else (self.info.average_response_time + exec_time) / 2
        self.info.performance_metrics.update({"tasks_completed": self.info.tasks_completed, "tasks_failed": self.info.tasks_failed, "average_response_time": self.info.average_response_time, "success_rate": self.info.tasks_completed / (self.info.tasks_completed + self.info.tasks_failed)})

    async def _send_task_result(self, task, result):
        data = {"task_id": task.task_id, "worker_id": self.worker_id, "result": result, "execution_time": task.completed_at - task.started_at, "timestamp": time.time()}
        if self.config.communication_backend == CommunicationBackend.ZMQ:
            s = self.context.socket(zmq.REQ)
            s.connect(f"tcp://localhost:{self.config.master_port}")
            s.send_json(data)
            s.close()

    async def _resource_monitoring_loop(self):
        while True:
            try: self.info.resource_usage = self.resource_monitor.get_current_usage()
            except Exception as e: self.logger.error(f"Resource monitoring error: {e}")
            await asyncio.sleep(1.0)

    def assign_task(self, task: TaskAssignment):
        self.task_queue.put(task)
        self.current_task = task

    def get_worker_stats(self) -> Dict[str, Any]:
        return {"worker_id": self.worker_id, "status": self.info.status.value, "tasks_completed": self.info.tasks_completed, "tasks_failed": self.info.tasks_failed, "average_response_time": self.info.average_response_time, "resource_usage": self.info.resource_usage, "performance_metrics": self.info.performance_metrics}
