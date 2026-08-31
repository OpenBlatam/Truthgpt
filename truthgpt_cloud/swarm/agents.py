"""
🐝 TruthGPT Cloud - Multi-Agent Swarm Personas & Nodes
Defines specialized autonomous research agent definitions for distributed reasoning.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SwarmAgentNode:
    agent_id: str
    role_name: str
    specialization: str
    status: str = "idle"  # "idle", "reasoning", "adversarial_audit", "verifying", "done"
    contribution: Optional[str] = None
    confidence: float = 0.98
    phase: int = 1


@dataclass
class DebateRound:
    round_number: int
    topic: str
    proponent_claim: str
    adversary_critique: str
    resolution: str
    cove_backtracking_triggered: bool = False


def get_default_swarm_nodes(max_agents: int = 5) -> List[SwarmAgentNode]:
    """Spawn standard multi-agent research personas based on quota."""
    nodes = [
        SwarmAgentNode(
            agent_id="agt_lead_theoretician",
            role_name="Lead Theoretical Scientist",
            specialization="Decomposición del problema y formulación de hipótesis matemáticas",
            status="reasoning",
            phase=1
        ),
        SwarmAgentNode(
            agent_id="agt_formal_verifier",
            role_name="Z3 Formal Logic & SMT Prover",
            specialization="Verificación de invariantes, contratos Hoare y teoremas",
            status="reasoning",
            phase=1
        ),
        SwarmAgentNode(
            agent_id="agt_code_synthesizer",
            role_name="High-Performance Systems Architect",
            specialization="Generación de algoritmos paralelos y optimización CUDA/TensorRT",
            status="reasoning",
            phase=1
        )
    ]
    
    if max_agents >= 4:
        nodes.append(
            SwarmAgentNode(
                agent_id="agt_paper_analyst",
                role_name="SOTA AI Literature Sentinel",
                specialization="Indexación y contraste con papers de NeurIPS/ICML/ArXiv",
                status="reasoning",
                phase=2
            )
        )
    if max_agents >= 5:
        nodes.append(
            SwarmAgentNode(
                agent_id="agt_consensus_arbiter",
                role_name="Quantum Consensus Arbiter",
                specialization="Votación ponderada, debate adversarial y eliminación de alucinaciones",
                status="reasoning",
                phase=3
            )
        )

    if max_agents > 5:
        for i in range(6, min(max_agents + 1, 101)):
            nodes.append(
                SwarmAgentNode(
                    agent_id=f"agt_parallel_solver_{i}",
                    role_name=f"Distributed Sub-Domain Solver #{i}",
                    specialization=f"Exploración de ramas de deducción paralela #{i}",
                    status="reasoning",
                    phase=2
                )
            )

    return nodes


__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "get_default_swarm_nodes",
]
