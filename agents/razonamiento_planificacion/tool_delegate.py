import logging
from typing import Any
from .tool_base import BaseTool

logger = logging.getLogger(__name__)

class DelegateTaskTool(BaseTool):
    """
    Delega una sub-tarea compleja a otro agente del enjambre.
    Acepta el nombre del agente y la tarea en formato 'agente:::tarea_a_completar'.
    Ejemplo: MarketingAgent:::Escribe un tweet sobre este resumen.
    Si no sabes qué agente usar, usa 'swarm', ej: swarm:::Crea un reporte de estos datos.
    """
    name = "delegate_task"

    def __init__(self, agent_client: Any = None):
        """Require AgentClient instance to allow recursive calling."""
        self.agent_client = agent_client

    async def run(self, cmd: str) -> str:
        if not self.agent_client:
            return "Error: DelegateTaskTool requiere una instancia de AgentClient."
            
        try:
            parts = cmd.split(":::", 1)
            if len(parts) != 2:
                return "Error: Formato inválido. Use 'agente:::tarea'."
            
            agent_target, task = parts
            agent_target = agent_target.strip()
            task = task.strip()
            
            logger.info(f"Delegando tarea a '{agent_target}': {task[:50]}...")
            
            # Isolated sub-memory namespace for the delegated task
            sub_user_id = f"delegate_{agent_target}_temp"
            
            # Run the task through the orchestrator/client
            # This allows hierarchical agent branching!
            result = await self.agent_client.run(user_id=sub_user_id, prompt=task)
            return f"Respuesta de {agent_target}:\n{result}"
        except Exception as e:
            return f"Error en delegación de tarea: {str(e)}"
