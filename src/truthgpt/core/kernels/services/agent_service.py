"""
AgentService - Manages AI agents and swarm operations
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base_service import BaseService


class AgentService(BaseService):
    """Service for managing AI agents and swarm orchestration"""

    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        super().__init__(kernel, config)
        self._agents: Dict[str, Any] = {}
        self._swarm_client = None

    async def _on_start(self) -> None:
        """Initialize agent subsystem"""
        try:
            import truthgpt.agents.framework.interfaces.client.client as ac
            import truthgpt.agents.framework.engines as ae
            engine_name = self.config.get("preferred_engine", "deepseek")
            llm = ae.engine_registry.get_engine(engine_name)
            self._swarm_client = ac.AgentClient(use_swarm=True, llm_engine=llm)
            self.logger.info(f"AgentService initialized with engine: {engine_name}")
        except Exception as e:
            self.logger.warning(f"AgentService partial init: {e}")

    async def _on_stop(self) -> None:
        """Cleanup agent resources"""
        self._agents.clear()
        self._swarm_client = None

    async def _get_health_info(self) -> Dict[str, Any]:
        return {
            "active_agents": len(self._agents),
            "swarm_ready": self._swarm_client is not None
        }

    def get_swarm_client(self):
        return self._swarm_client

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())
