"""
Blockchain Agent - System 5.9
============================
Specialized agent for Web3, DeFi auditing, and Smart Contract interaction.
"""

import logging
from typing import Optional, Dict, Any
from optimization_core.agents.framework.architectures.base_agent import BaseAgent
from optimization_core.agents.framework.models import AgentResponse
from .hub import BlockchainHub

logger = logging.getLogger(__name__)

class BlockchainAgent(BaseAgent):
    """
    Expert Agent for Blockchain Intelligence.
    Can analyze wallets, audit contracts, and monitor DeFi protocols.
    """
    
    def __init__(self, config=None, llm_engine=None):
        super().__init__(
            name="blockchain_agent",
            role="Web3 & Smart Contract Intelligence"
        )
        self.config = config
        self.llm_engine = llm_engine
        self.hub = BlockchainHub()
        self.expertise = "Web3, DeFi auditing, and Smart Contract interaction"

    async def process(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Processes blockchain-related requests.
        """
        system_prompt = (
            f"You are the TruthGPT Blockchain Agent.\n"
            f"Role: {self.role}\n"
            f"Expertise: {self.expertise}.\n\n"
            f"Task: Analyze the user request and provide deep blockchain insights.\n"
            f"If the user provides an address, audit its balance and transactions via your Hub."
        )
        
        full_query = f"{system_prompt}\nUser Request: {prompt}"
        
        if self.llm_engine is not None:
            try:
                import inspect
                if inspect.iscoroutinefunction(self.llm_engine):
                    llm_output = await self.llm_engine(full_query)
                else:
                    llm_output = self.llm_engine(full_query)
                content = str(llm_output)
            except Exception as exc:
                logger.error("BlockchainAgent LLM execution failed: %s", exc)
                content = f"[Blockchain Agent Error]: Failed to query LLM engine: {exc}"
        else:
            content = f"Blockchain Intelligence Analysis for query: '{prompt}'. Hub initialized and active."

        self.add_to_memory("user", prompt)
        self.add_to_memory("assistant", content)

        return AgentResponse.success(
            content=content,
            metadata={"agent": self.name, "role": self.role, "context": context or {}},
        )

