import asyncio
from typing import List, Dict, Callable
from loguru import logger
from .base_service import BaseService

class AgentProcess:
    """Representa un 'Proceso' aislado en el AIOS."""
    def __init__(self, agent_id: str, priority: int = 1):
        self.agent_id = agent_id
        self.priority = priority
        self.state = "READY"

class AgentScheduler:
    """
    Implementación basada en el paper 'AIOS: LLM Agent Operating System'.
    Planifica la ejecución concurrente de agentes, aislando recursos y contexto.
    """
    def __init__(self):
        self.process_queue: List[AgentProcess] = []
        self.active_processes: Dict[str, AgentProcess] = {}

    def spawn_agent(self, agent_id: str, priority: int) -> AgentProcess:
        process = AgentProcess(agent_id, priority)
        self.process_queue.append(process)
        self.process_queue.sort(key=lambda p: p.priority, reverse=True) # Priority Scheduling
        logger.info(f"[AgentService/Scheduler] Spawned new agent process: {agent_id} (Priority: {priority})")
        return process

    async def context_switch(self, current: AgentProcess, next_p: AgentProcess):
        """Simula el cambio de contexto entre agentes para evitar contaminación en el LLM."""
        logger.debug(f"[AgentService/Scheduler] Context switch: Suspending {current.agent_id} -> Resuming {next_p.agent_id}")
        current.state = "SUSPENDED"
        next_p.state = "RUNNING"
        await asyncio.sleep(0.05) # Overhead de cambio de contexto de memoria

class AgentService(BaseService):
    """
    Servicio de gestión de Agentes estilo SO (AIOS).
    Aisla la memoria y herramienta de cada agente como si fueran procesos de Linux.
    """
    def __init__(self):
        super().__init__("AgentService")
        self.scheduler = AgentScheduler()

    async def _on_start(self):
        logger.info("[AgentService] Initializing AIOS Agent Scheduler (Priority-based).")
        await asyncio.sleep(0.1)

    async def _on_stop(self):
        logger.info("[AgentService] Terminating all active agent processes.")
        self.scheduler.process_queue.clear()
        self.scheduler.active_processes.clear()

    async def dispatch_task(self, agent_id: str, priority: int = 1):
        """Encola y ejecuta un agente usando el Scheduler."""
        process = self.scheduler.spawn_agent(agent_id, priority)
        process.state = "RUNNING"
        self.scheduler.active_processes[agent_id] = process
        
        logger.info(f"[AgentService] Executing task for process {agent_id}...")
        # Aquí se conectaría con ModelService para el procesamiento real
        await asyncio.sleep(0.2)
        
        process.state = "TERMINATED"
        logger.info(f"[AgentService] Process {agent_id} terminated successfully.")
        del self.scheduler.active_processes[agent_id]
