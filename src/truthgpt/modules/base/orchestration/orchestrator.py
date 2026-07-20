import logging
import time
import networkx as nx
from typing import Dict, List, Any, Callable
from collections import defaultdict

from .base import AgentConfig, Task, MetaLearningConfig, MetaLearningStrategy
from .agent import AIAgent
from .engine import MetaLearningEngine

class AIOrchestrator:
    """Advanced AI orchestrator for TruthGPT"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"AIOrchestrator_{id(self)}")
        self.agents = {}
        self.agent_graph = nx.Graph()
        self.task_queue = []
        self.completed_tasks = []
        self.task_dependencies = {}
        self.meta_learning_engine = MetaLearningEngine(MetaLearningConfig(strategy=MetaLearningStrategy.MODEL_AGNOSTIC_META_LEARNING))
        self.coordination_strategies = {}
        self._init_coordination_strategies()
        self.orchestration_metrics = {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "average_execution_time": 0.0, "agent_utilization": {}, "collaboration_count": 0}
    
    def _init_coordination_strategies(self):
        self.coordination_strategies = {"load_balancing": self._load_balancing_strategy, "specialization": self._specialization_strategy, "collaboration": self._collaboration_strategy, "priority_based": self._priority_based_strategy}
    
    def add_agent(self, config: AgentConfig) -> str:
        self.agents[config.agent_id] = AIAgent(config)
        self.agent_graph.add_node(config.agent_id, **config.__dict__)
        return config.agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.agent_graph.remove_node(agent_id)
            return True
        return False
    
    def add_task(self, task: Task) -> str:
        self.task_queue.append(task)
        self.orchestration_metrics["total_tasks"] += 1
        if task.dependencies: self.task_dependencies[task.task_id] = task.dependencies
        return task.task_id
    
    async def execute_orchestration(self, strategy: str = "load_balancing") -> Dict[str, Any]:
        start_time = time.time()
        func = self.coordination_strategies.get(strategy, self._load_balancing_strategy)
        res = await func()
        self.orchestration_metrics["average_execution_time"] = time.time() - start_time
        self.orchestration_metrics["completed_tasks"] += len(res.get("completed_tasks", []))
        return {"strategy": strategy, "execution_time": self.orchestration_metrics["average_execution_time"], "tasks_processed": len(self.task_queue) + len(res.get("completed_tasks", [])), "agents_utilized": len(self.agents), "orchestration_result": res, "metrics": self.orchestration_metrics}

    async def _load_balancing_strategy(self):
        completed = []
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        for task in self.task_queue[:]:
            agent_id = self._find_best_agent_for_task(task)
            if agent_id:
                try:
                    res = await self.agents[agent_id].execute_task(task)
                    task.status = "completed"
                    completed.append(task)
                    self.task_queue.remove(task)
                    self.meta_learning_engine.store_experience(task, res, agent_id)
                except Exception as e:
                    self.logger.error(f"Task {task.task_id} failed: {e}")
                    task.status = "failed"
                    self.orchestration_metrics["failed_tasks"] += 1
        return {"strategy": "load_balancing", "completed_tasks": completed, "remaining_tasks": len(self.task_queue)}

    async def _specialization_strategy(self):
        completed = []
        spec = defaultdict(list)
        for aid, a in self.agents.items():
            for c in a.config.capabilities: spec[c].append(aid)
        for task in self.task_queue[:]:
            agent_id = next((spec[c][0] for c in task.required_capabilities if c in spec and spec[c]), None)
            if agent_id:
                try:
                    await self.agents[agent_id].execute_task(task)
                    task.status = "completed"
                    completed.append(task)
                    self.task_queue.remove(task)
                except Exception as e:
                    self.logger.error(f"Task {task.task_id} failed: {e}")
                    task.status = "failed"
        return {"strategy": "specialization", "completed_tasks": completed}

    async def _collaboration_strategy(self): return {"strategy": "collaboration", "status": "not_implemented"}
    async def _priority_based_strategy(self): return await self._load_balancing_strategy()

    def _find_best_agent_for_task(self, task: Task) -> Optional[str]:
        # Simplified: find agent with least current tasks
        if not self.agents: return None
        return min(self.agents.keys(), key=lambda aid: len(self.agents[aid].state.current_tasks))
