"""
🐝 TruthGPT Cloud - Client Swarm Mixin
Provides multi-agent swarm orchestration, adversarial debate, and Tree-of-Thoughts client methods.
"""

from typing import Dict, Optional, Any
from ..swarm.orchestrator import SwarmExecutionTrace
from ..swarm.models import TreeOfThoughtsTrace
from .http_layer import _run_sync


class ClientSwarmMixin:
    """Mixin encapsulating autonomous swarm and collective reasoning client SDK methods."""

    async def run_swarm_async(
        self,
        prompt: str,
        max_agents: Optional[int] = None,
        topology: Optional[str] = None
    ) -> SwarmExecutionTrace:
        """Execute an autonomous multi-agent swarm research cycle asynchronously."""
        tier_cfg = self.tier_config
        num_agents = max_agents if max_agents is not None else tier_cfg.max_swarm_agents
        top = topology or "hierarchical"
        return await self.swarm.execute_swarm_session(
            prompt=prompt,
            user_id=self.user_id,
            max_agents=num_agents,
            depth_level=tier_cfg.smt_z3_verification_depth,
            topology=top
        )

    def run_swarm(
        self,
        prompt: str,
        max_agents: Optional[int] = None,
        topology: Optional[str] = None
    ) -> SwarmExecutionTrace:
        """Execute an autonomous multi-agent swarm research cycle synchronously."""
        return _run_sync(self.run_swarm_async(prompt, max_agents, topology=topology))

    def execute_adversarial_debate(
        self,
        topic: str,
        proponent_claim: str,
        adversary_focus: str = "Búsqueda de singularidades y contraejemplos",
        rounds: int = 2
    ) -> Dict[str, Any]:
        """Execute a formal Red Team vs Blue Team adversarial debate session."""
        if getattr(self, "_is_remote", False):
            payload = {
                "topic": topic,
                "proponent_claim": proponent_claim,
                "adversary_focus": adversary_focus,
                "rounds": rounds,
                "user_id": self.user_id,
            }
            return self.http_post("/api/v1/cloud/swarm/debate", json_data=payload)
        return _run_sync(
            self.swarm.execute_adversarial_debate(
                topic=topic,
                proponent_claim=proponent_claim,
                adversary_focus=adversary_focus,
                rounds=rounds,
                user_id=self.user_id
            )
        )

    async def run_tree_of_thoughts_async(
        self,
        prompt: str,
        max_depth: int = 3,
        branching_factor: int = 3,
        min_confidence_threshold: float = 0.70
    ) -> TreeOfThoughtsTrace:
        """Execute Tree-of-Thoughts exploratory swarm reasoning asynchronously."""
        return await self.swarm.run_tree_of_thoughts(
            prompt=prompt,
            max_depth=max_depth,
            branching_factor=branching_factor,
            min_confidence_threshold=min_confidence_threshold,
            user_id=self.user_id
        )

    def run_tree_of_thoughts(
        self,
        prompt: str,
        max_depth: int = 3,
        branching_factor: int = 3,
        min_confidence_threshold: float = 0.70
    ) -> TreeOfThoughtsTrace:
        """Execute Tree-of-Thoughts exploratory swarm reasoning synchronously."""
        return _run_sync(
            self.run_tree_of_thoughts_async(
                prompt=prompt,
                max_depth=max_depth,
                branching_factor=branching_factor,
                min_confidence_threshold=min_confidence_threshold
            )
        )

    def visualize_swarm(self, session_id: str) -> str:
        """Retrieve trace from session ID and render its Mermaid diagram."""
        trace = self.swarm.get_session_trace(session_id)
        if not trace:
            raise ValueError(f"Swarm session trace '{session_id}' not found.")
        return trace.to_mermaid()

    def render_swarm_topology_mermaid(self, topology: str = "hierarchical") -> str:
        """Render a Mermaid definition for a specific swarm coordination topology."""
        return self.swarm.render_topology_mermaid(topology=topology)

    # Aliases
    tree_of_thoughts = run_tree_of_thoughts
    tot = run_tree_of_thoughts


__all__ = ["ClientSwarmMixin"]
