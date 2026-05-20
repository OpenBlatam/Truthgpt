import logging
import uuid
import random
import time
from typing import List, Dict, Any, Callable
from collections import deque
import torch
import torch.nn as nn

from .base import MetaLearningConfig, MetaLearningStrategy, Task, TaskType
from .agent import AIAgent

class MetaLearningEngine:
    """Meta-learning engine for TruthGPT"""
    
    def __init__(self, config: MetaLearningConfig):
        self.config = config
        self.logger = logging.getLogger(f"MetaLearningEngine_{id(self)}")
        self.task_memory = {}
        self.model_memory = {}
        self.adaptation_strategies = {}
        self._init_meta_learning_strategy()
        self.meta_learning_history = []
        self.memory_bank = deque(maxlen=self.config.memory_bank_size)
    
    def _init_meta_learning_strategy(self):
        if self.config.strategy == MetaLearningStrategy.MODEL_AGNOSTIC_META_LEARNING:
            self.meta_learner = nn.Sequential(nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 32))
            self.meta_optimizer = torch.optim.Adam(self.meta_learner.parameters(), lr=self.config.meta_learning_rate)
        elif self.config.strategy == MetaLearningStrategy.GRADIENT_BASED_META_LEARNING:
            self.gradient_learner = nn.Sequential(nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 32))
        elif self.config.strategy == MetaLearningStrategy.MEMORY_BASED_META_LEARNING:
            self.similarity_threshold = self.config.task_similarity_threshold

    async def meta_learn(self, tasks: List[Task], agents: List[AIAgent]) -> Dict[str, Any]:
        self.logger.info(f"Starting meta-learning with {len(tasks)} tasks")
        results = {"strategy": self.config.strategy.value, "tasks_processed": len(tasks), "agents_involved": len(agents), "adaptations": []}
        groups = self._group_tasks_by_similarity(tasks)
        for group_id, group_tasks in groups.items():
            results["adaptations"].append(await self._meta_learn_task_group(group_tasks, agents))
        self.meta_learning_history.append(results)
        return results

    def _group_tasks_by_similarity(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        groups = {}
        for task in tasks:
            similar_group = next((gid for gid, gtasks in groups.items() if self._calculate_task_similarity(task, gtasks[0]) > self.config.task_similarity_threshold), None)
            if similar_group: groups[similar_group].append(task)
            else: groups[str(uuid.uuid4())] = [task]
        return groups

    def _calculate_task_similarity(self, t1: Task, t2: Task) -> float:
        type_sim = 1.0 if t1.task_type == t2.task_type else 0.0
        comp_sim = 1.0 - abs(t1.complexity - t2.complexity)
        cap1, cap2 = set(t1.required_capabilities), set(t2.required_capabilities)
        cap_sim = len(cap1 & cap2) / max(len(cap1 | cap2), 1)
        return 0.4 * type_sim + 0.3 * comp_sim + 0.3 * cap_sim

    async def _meta_learn_task_group(self, tasks: List[Task], agents: List[AIAgent]) -> Dict[str, Any]:
        if self.config.strategy == MetaLearningStrategy.MODEL_AGNOSTIC_META_LEARNING: return await self._maml_adaptation(tasks, agents)
        if self.config.strategy == MetaLearningStrategy.MEMORY_BASED_META_LEARNING: return await self._memory_based_adaptation(tasks, agents)
        return {"adaptation_type": "generic", "tasks_adapted": len(tasks), "agents_involved": len(agents), "success": True}

    async def _maml_adaptation(self, tasks, agents):
        steps = [{"step": i, "loss": random.uniform(0.1, 0.5) * (1 - i / self.config.inner_loop_steps), "adaptation_rate": self.config.meta_learning_rate} for i in range(self.config.inner_loop_steps)]
        return {"adaptation_type": "maml", "inner_loop_steps": self.config.inner_loop_steps, "adaptation_steps": steps, "final_loss": steps[-1]["loss"]}

    async def _memory_based_adaptation(self, tasks, agents):
        similar = [e for t in tasks for e in self.memory_bank if self._calculate_task_similarity(t, e.get("task", Task("", TaskType.TRAINING))) > self.config.task_similarity_threshold]
        return {"adaptation_type": "memory_based", "similar_experiences": len(similar), "memory_size": len(self.memory_bank), "confidence": min(len(similar) / max(len(tasks), 1), 1.0)}

    def store_experience(self, task: Task, result: Dict[str, Any], agent_id: str):
        self.memory_bank.append({"task": task, "result": result, "agent_id": agent_id, "timestamp": time.time(), "success": result.get("success", True)})

    def get_meta_learning_stats(self) -> Dict[str, Any]:
        return {"strategy": self.config.strategy.value, "memory_size": len(self.memory_bank), "adaptations_performed": len(self.meta_learning_history), "task_memory_size": len(self.task_memory), "model_memory_size": len(self.model_memory)}
