"""
Planning & Orchestration Agent - System 5.9
==========================================
Wraps the SwarmOrchestrator to provide a standard agent interface.
"""

import logging
from typing import Optional, Dict, Any
from ..arquitecturas_fundamentales.base_agent import BaseAgent
from .swarm_orchestrator import SwarmOrchestrator, SwarmConfig

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """
    Expert Agent for Strategic Planning and Swarm Orchestration.
    """
    
    def __init__(self, config=None, llm_engine=None):
        super().__init__(
            name="planning_agent",
            role="Strategic Planning & Multi-Agent Coordination"
        )
        self.config = config
        self.llm_engine = llm_engine
        self.orchestrator = SwarmOrchestrator(
            llm_engine=llm_engine,
            swarm_config=SwarmConfig()
        )

    async def process(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Delegates the request to the internal swarm orchestrator.
        """
        # If the orchestrator has no agents, it can still act as a planner
        if not self.orchestrator.agents:
            # Simple planning logic via LLM
            plan_prompt = f"Develop a strategic plan for: {prompt}"
            response = await self.llm_engine(plan_prompt)
            from ..models import AgentResponse
            return AgentResponse(content=response, action_type="final_answer")
            
        return await self.orchestrator.route_and_process(prompt, context)

    def register_agent(self, agent: BaseAgent):
        """Allows registering sub-agents for orchestration."""
        self.orchestrator.register_agent(agent)
