import logging
import time
import uuid
import random
import asyncio
from typing import Dict, List, Any, Optional, Set
from collections import deque
import torch.nn as nn
import numpy as np

from .base import AgentConfig, AgentState, AgentStatus, AgentType, Task, TaskType

class AIAgent:
    """Individual AI agent for orchestration"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"AIAgent_{config.agent_id}")
        self.state = AgentState(agent_id=config.agent_id)
        self.meta_learner: Optional[nn.Module] = None
        self._init_specialized_components()
        self.message_queue = deque()
        self.collaboration_network = set()
        self.performance_history = []
    
    def _init_specialized_components(self):
        if self.config.agent_type == AgentType.LEARNING_AGENT:
            pass
        elif self.config.agent_type == AgentType.OPTIMIZATION_AGENT:
            self.optimization_model = nn.Sequential(nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        elif self.config.agent_type == AgentType.EVALUATION_AGENT:
            self.evaluation_metrics = {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "perplexity": 0.0}
        elif self.config.agent_type == AgentType.META_LEARNING_AGENT:
            self.meta_learner = nn.Sequential(nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 32))
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        self.logger.info(f"Agent {self.config.agent_id} executing task {task.task_id}")
        self.state.status = AgentStatus.BUSY
        self.state.current_tasks.append(task.task_id)
        self.state.last_activity = time.time()
        
        try:
            if task.task_type == TaskType.TRAINING: result = await self._execute_training_task(task)
            elif task.task_type == TaskType.INFERENCE: result = await self._execute_inference_task(task)
            elif task.task_type == TaskType.OPTIMIZATION: result = await self._execute_optimization_task(task)
            elif task.task_type == TaskType.EVALUATION: result = await self._execute_evaluation_task(task)
            elif task.task_type == TaskType.META_LEARNING: result = await self._execute_meta_learning_task(task)
            else: result = await self._execute_generic_task(task)
            
            self._update_performance_metrics(task, result)
            self.state.current_tasks.remove(task.task_id)
            self.state.completed_tasks.append(task.task_id)
            self.state.status = AgentStatus.IDLE
            return result
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            self.state.status = AgentStatus.ERROR
            if task.task_id in self.state.current_tasks: self.state.current_tasks.remove(task.task_id)
            raise

    async def _execute_training_task(self, task: Task) -> Dict[str, Any]:
        epochs = task.data.get("epochs", 10)
        history = [{"epoch": i, "loss": random.uniform(0.1, 1.0) * (1 - i / epochs)} for i in range(epochs)]
        return {"task_type": "training", "epochs": epochs, "final_loss": history[-1]["loss"], "training_history": history}

    async def _execute_inference_task(self, task: Task) -> Dict[str, Any]:
        return {"task_type": "inference", "input": task.data.get("input_data", ""), "output": f"Inferred result for: {task.data.get('input_data', '')}", "confidence": random.uniform(0.7, 0.95)}

    async def _execute_optimization_task(self, task: Task) -> Dict[str, Any]:
        return {"task_type": "optimization", "target": task.data.get("target", "performance"), "iterations": task.data.get("iterations", 100), "best_value": random.uniform(0.5, 1.0), "improvement": random.uniform(0.1, 0.3)}

    async def _execute_evaluation_task(self, task: Task) -> Dict[str, Any]:
        return {"task_type": "evaluation", "metrics": {"accuracy": random.uniform(0.8, 0.95), "precision": random.uniform(0.75, 0.9), "recall": random.uniform(0.7, 0.85), "f1_score": random.uniform(0.75, 0.9), "perplexity": random.uniform(2.0, 5.0)}, "test_samples": len(task.data.get("test_data", []))}

    async def _execute_meta_learning_task(self, task: Task) -> Dict[str, Any]:
        return {"task_type": "meta_learning", "adaptation_steps": random.randint(3, 10), "meta_loss": random.uniform(0.1, 0.5), "support_samples": len(task.data.get("support_set", [])), "query_samples": len(task.data.get("query_set", []))}

    async def _execute_generic_task(self, task: Task) -> Dict[str, Any]:
        return {"task_type": task.task_type.value, "status": "completed", "result": f"Generic task {task.task_id} completed"}

    def _update_performance_metrics(self, task: Task, result: Dict[str, Any]):
        metrics = {"task_id": task.task_id, "task_type": task.task_type.value, "execution_time": time.time() - task.created_at, "success": True, "timestamp": time.time()}
        if task.task_type == TaskType.TRAINING: metrics["final_loss"] = result.get("final_loss", 0.0)
        elif task.task_type == TaskType.INFERENCE: metrics["confidence"] = result.get("confidence", 0.0)
        elif task.task_type == TaskType.EVALUATION: metrics["accuracy"] = result.get("metrics", {}).get("accuracy", 0.0)
        self.performance_history.append(metrics)
        if "accuracy" in metrics: self.state.performance_metrics["accuracy"] = metrics["accuracy"]
        self.state.performance_metrics["avg_execution_time"] = np.mean([p.get("execution_time", 0) for p in self.performance_history[-10:]])

    async def collaborate_with_agent(self, other_agent_id: str, task: Task) -> Dict[str, Any]:
        self.state.collaboration_history[other_agent_id] = self.state.collaboration_history.get(other_agent_id, 0) + 1
        return {"collaboration_id": str(uuid.uuid4()), "agents": [self.config.agent_id, other_agent_id], "task_id": task.task_id, "collaboration_type": "joint_execution", "result": "collaboration_successful"}

    def get_agent_info(self) -> Dict[str, Any]:
        return {"agent_id": self.config.agent_id, "agent_type": self.config.agent_type.value, "status": self.state.status.value, "capabilities": self.config.capabilities, "current_tasks": len(self.state.current_tasks), "completed_tasks": len(self.state.completed_tasks), "performance_metrics": self.state.performance_metrics, "collaboration_count": len(self.state.collaboration_history), "last_activity": self.state.last_activity}
