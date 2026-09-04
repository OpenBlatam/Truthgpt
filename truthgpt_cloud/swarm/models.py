"""
🐝 TruthGPT Cloud - Swarm Data Models
Defines agent nodes, debate rounds, and execution trace artifacts for multi-agent swarm orchestration.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class SwarmAgentNode:
    agent_id: str
    role_name: str
    specialization: str
    status: str = "idle"  # "idle", "reasoning", "adversarial_audit", "verifying", "done"
    contribution: Optional[str] = None
    reasoning_steps: List[str] = field(default_factory=list)
    confidence: float = 0.98
    phase: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "specialization": self.specialization,
            "status": self.status,
            "contribution": self.contribution,
            "reasoning_steps": self.reasoning_steps,
            "confidence": self.confidence,
            "phase": self.phase
        }


@dataclass
class DebateRound:
    round_number: int
    topic: str
    proponent_claim: str
    adversary_critique: str
    resolution: str
    cove_backtracking_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "topic": self.topic,
            "proponent_claim": self.proponent_claim,
            "adversary_critique": self.adversary_critique,
            "resolution": self.resolution,
            "cove_backtracking_triggered": self.cove_backtracking_triggered
        }


@dataclass
class SwarmExecutionTrace:
    session_id: str
    user_id: str
    prompt: str
    agents_involved: List[SwarmAgentNode]
    consensus_summary: str
    execution_time_ms: float
    total_tokens: int
    formal_invariants_checked: int
    topology: str = "hierarchical"
    debate_rounds: List[DebateRound] = field(default_factory=list)
    cove_backtracking_count: int = 0
    confidence_aggregate: float = 0.998
    consensus_score: float = 0.998

    def to_mermaid_graph(self) -> str:
        """Generate a Mermaid diagram representing the multi-agent swarm debate topology."""
        lines = [
            "graph TD",
            f'    Prompt["💬 Query: {self.prompt[:35]}..."]',
            f'    Consensus["👑 Consensus Score: {self.consensus_score * 100:.1f}%"]',
        ]
        for idx, agt in enumerate(self.agents_involved):
            clean_role = agt.role_name.replace('"', "'")
            lines.append(f'    Agent_{idx}["🐝 {clean_role}<br/>Conf: {agt.confidence * 100:.1f}%"]')
            lines.append(f"    Prompt --> Agent_{idx}")
            lines.append(f"    Agent_{idx} --> Consensus")
        return "\n".join(lines)

    def to_reasoning_dag(self) -> Dict[str, Any]:
        """Export the swarm execution structure as a directed acyclic reasoning graph (DAG)."""
        nodes = [{"id": "prompt", "label": self.prompt, "type": "input"}]
        edges = []
        for i, a in enumerate(self.agents_involved):
            agt_id = f"agent_{i}_{a.agent_id}"
            nodes.append({
                "id": agt_id,
                "label": a.role_name,
                "contribution": a.contribution,
                "confidence": a.confidence,
                "status": a.status,
                "type": "agent_node"
            })
            edges.append({"source": "prompt", "target": agt_id})
            edges.append({"source": agt_id, "target": "consensus"})

        nodes.append({
            "id": "consensus",
            "label": self.consensus_summary,
            "score": self.consensus_score,
            "type": "output"
        })

        return {
            "session_id": self.session_id,
            "topology": self.topology,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "topology": self.topology,
            "agents_involved": [a.to_dict() if hasattr(a, "to_dict") else asdict(a) for a in self.agents_involved],
            "consensus_summary": self.consensus_summary,
            "execution_time_ms": self.execution_time_ms,
            "total_tokens": self.total_tokens,
            "formal_invariants_checked": self.formal_invariants_checked,
            "debate_rounds": [d.to_dict() if hasattr(d, "to_dict") else asdict(d) for d in self.debate_rounds],
            "cove_backtracking_count": self.cove_backtracking_count,
            "confidence_aggregate": self.confidence_aggregate,
            "consensus_score": self.consensus_score
        }


__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "SwarmExecutionTrace",
]
