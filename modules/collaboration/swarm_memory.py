"""
🧠 SwarmMemory - Shared Distributed Knowledge Base
==================================================
Allows nodes to broadcast facts, research findings, and 
contextual snippets across the Global Swarm Network.
"""
import asyncio
import logging
from typing import Dict, List, Any

logger = logging.getLogger("collaboration.memory")

class SwarmMemory:
    def __init__(self):
        # Local cache of shared knowledge
        self.facts: Dict[str, str] = {}
        self.last_update = 0.0

    def add_fact(self, key: str, value: str):
        """Add or update a fact in the shared memory."""
        self.facts[key] = value
        self.last_update = asyncio.get_event_loop().time()

    def get_knowledge_summary(self) -> str:
        """Returns a summarized string of shared knowledge for LLM context."""
        if not self.facts:
            return "No shared knowledge available."
        
        summary = "Shared Swarm Intelligence:\n"
        for k, v in self.facts.items():
            summary += f"- {k}: {v}\n"
        return summary

    def clear(self):
        self.facts.clear()
