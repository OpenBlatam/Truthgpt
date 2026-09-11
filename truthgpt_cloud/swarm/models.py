"""
🐝 TruthGPT Cloud - Swarm Data Models
Defines agent nodes, debate rounds, and execution trace artifacts for multi-agent swarm orchestration.
"""

import uuid
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
    latency_ms: float = 0.0
    tokens_consumed: int = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "specialization": self.specialization,
            "status": self.status,
            "contribution": self.contribution,
            "reasoning_steps": self.reasoning_steps,
            "confidence": self.confidence,
            "phase": self.phase,
            "latency_ms": self.latency_ms,
            "tokens_consumed": self.tokens_consumed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
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
    trace_id: str = ""
    parent_trace_id: Optional[str] = None
    agent_latencies: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = f"trace_swm_{uuid.uuid4().hex[:16]}"
        if not self.agent_latencies and self.agents_involved:
            for a in self.agents_involved:
                if hasattr(a, "agent_id") and hasattr(a, "latency_ms"):
                    self.agent_latencies[a.agent_id] = a.latency_ms

    def to_mermaid(self) -> str:
        """Alias for to_mermaid_graph generating rich Mermaid diagram of the swarm trace."""
        lines = [
            "graph TD",
            f'    Prompt["💬 Query: {self.prompt[:40]}..."]',
            f'    Consensus["👑 Consensus Score: {self.consensus_score * 100:.1f}%"]',
        ]
        for idx, agt in enumerate(self.agents_involved):
            clean_role = agt.role_name.replace('"', "'")
            lines.append(f'    Agent_{idx}["🐝 {clean_role}<br/>Conf: {agt.confidence * 100:.1f}%"]')
            lines.append(f"    Prompt --> Agent_{idx}")
            lines.append(f"    Agent_{idx} --> Consensus")
        if self.debate_rounds:
            for d in self.debate_rounds:
                r_id = f"Round_{d.round_number}"
                lines.append(f'    {r_id}{{"⚖️ Round {d.round_number}: {d.topic[:30]}..."}}')
                lines.append(f"    Consensus -.-> {r_id}")
        return "\n".join(lines)

    def to_mermaid_graph(self) -> str:
        """Generate a Mermaid diagram representing the multi-agent swarm debate topology."""
        return self.to_mermaid()

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

    def to_opentelemetry_spans(self) -> List[Dict[str, Any]]:
        """
        Export swarm execution trace to OpenTelemetry-compatible span dictionaries.
        """
        spans = []
        root_span_id = f"span_{self.session_id[-16:]}" if len(self.session_id) >= 16 else f"span_{self.session_id}"
        root_span = {
            "trace_id": self.trace_id,
            "span_id": root_span_id,
            "parent_span_id": self.parent_trace_id,
            "name": f"swarm_execution_{self.topology}",
            "kind": "SERVER",
            "duration_ms": self.execution_time_ms,
            "attributes": {
                "swarm.session_id": self.session_id,
                "swarm.user_id": self.user_id,
                "swarm.topology": self.topology,
                "swarm.total_tokens": self.total_tokens,
                "swarm.agents_count": len(self.agents_involved),
                "swarm.consensus_score": self.consensus_score,
                "swarm.formal_invariants": self.formal_invariants_checked,
            },
            "status": {"code": "OK"},
        }
        spans.append(root_span)

        for agent in self.agents_involved:
            agent_span = {
                "trace_id": self.trace_id,
                "span_id": f"span_{agent.agent_id[-12:]}" if len(agent.agent_id) >= 12 else f"span_{agent.agent_id}",
                "parent_span_id": root_span_id,
                "name": f"agent_node:{agent.role_name}",
                "kind": "INTERNAL",
                "duration_ms": agent.latency_ms or (self.execution_time_ms / max(len(self.agents_involved), 1)),
                "attributes": {
                    "agent.id": agent.agent_id,
                    "agent.role": agent.role_name,
                    "agent.specialization": agent.specialization,
                    "agent.confidence": agent.confidence,
                    "agent.tokens": agent.tokens_consumed,
                    "agent.status": agent.status,
                },
                "status": {"code": "ERROR" if agent.error else "OK"},
            }
            spans.append(agent_span)

        return spans

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "parent_trace_id": self.parent_trace_id,
            "agent_latencies": self.agent_latencies,
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


@dataclass
class ThoughtNode:
    node_id: str
    parent_id: Optional[str]
    depth: int
    thought: str
    confidence: float = 0.95
    status: str = "explored"  # "explored", "pruned", "selected", "backtracked"
    verification_feedback: Optional[str] = None
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "thought": self.thought,
            "confidence": self.confidence,
            "status": self.status,
            "verification_feedback": self.verification_feedback,
            "agent_id": self.agent_id,
        }


@dataclass
class TreeOfThoughtsTrace:
    session_id: str
    root_query: str
    max_depth: int
    branching_factor: int
    total_nodes_explored: int
    pruned_branches_count: int
    backtracking_events_count: int
    execution_time_ms: float
    selected_path: List[ThoughtNode]
    all_nodes: List[ThoughtNode]
    consensus_solution: str
    confidence_score: float = 0.995

    def to_mermaid(self) -> str:
        """Render Tree-of-Thoughts tree in Mermaid graph TD format with status highlighting."""
        lines = [
            "graph TD",
            f'    Root["💬 Root Query: {self.root_query[:40]}..."]',
        ]
        for n in self.all_nodes:
            clean_thought = n.thought.replace('"', "'")[:40] + ("..." if len(n.thought) > 40 else "")
            icon = "✅" if n.status == "selected" else ("❌" if n.status == "pruned" else "↩️" if n.status == "backtracked" else "💡")
            label = f'{icon} [{n.status.upper()}] d={n.depth}<br/>{clean_thought}<br/>Conf: {n.confidence*100:.1f}%'
            lines.append(f'    {n.node_id}["{label}"]')
            if n.parent_id and n.parent_id != "root":
                lines.append(f"    {n.parent_id} --> {n.node_id}")
            else:
                lines.append(f"    Root --> {n.node_id}")

        lines.append(f'    Solution["🏆 Verified Solution<br/>Conf: {self.confidence_score*100:.1f}%"]')
        if self.selected_path:
            last_selected = self.selected_path[-1]
            lines.append(f"    {last_selected.node_id} ==> Solution")
        else:
            lines.append("    Root ==> Solution")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "root_query": self.root_query,
            "max_depth": self.max_depth,
            "branching_factor": self.branching_factor,
            "total_nodes_explored": self.total_nodes_explored,
            "pruned_branches_count": self.pruned_branches_count,
            "backtracking_events_count": self.backtracking_events_count,
            "execution_time_ms": self.execution_time_ms,
            "selected_path": [n.to_dict() for n in self.selected_path],
            "all_nodes": [n.to_dict() for n in self.all_nodes],
            "consensus_solution": self.consensus_solution,
            "confidence_score": self.confidence_score,
            "mermaid_graph": self.to_mermaid(),
        }


__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "SwarmExecutionTrace",
    "ThoughtNode",
    "TreeOfThoughtsTrace",
]

