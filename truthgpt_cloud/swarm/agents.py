"""
🐝 TruthGPT Cloud - Multi-Agent Swarm Personas & Nodes
Defines specialized autonomous research agent definitions for distributed reasoning.
"""

from typing import List

from .models import SwarmAgentNode, DebateRound


def get_default_swarm_nodes(max_agents: int = 5) -> List[SwarmAgentNode]:
    """Spawn standard multi-agent research personas based on quota."""
    nodes = [
        SwarmAgentNode(
            agent_id="agt_lead_theoretician",
            role_name="Lead Theoretical Scientist",
            specialization="Descomposición axiomática y formulación rigurosa de hipótesis matemáticas",
            status="reasoning",
            reasoning_steps=[
                "Descomposición del enunciado en lemas fundamentales",
                "Formulación de invariantes y precondiciones de frontera",
                "Construcción del grafo de dependencias axiomáticas"
            ],
            confidence=0.995,
            phase=1
        ),
        SwarmAgentNode(
            agent_id="agt_formal_verifier",
            role_name="Z3 Formal Logic & SMT Prover",
            specialization="Verificación formal de invariantes, cláusulas SMT y contratos Hoare",
            status="reasoning",
            reasoning_steps=[
                "Traducción a AST de cláusulas de primer orden para Z3 SMT",
                "Comprobación de satisfacibilidad y búsqueda de refutación",
                "Emisión de hash de raíz Merkle SHA-256"
            ],
            confidence=0.999,
            phase=1
        ),
        SwarmAgentNode(
            agent_id="agt_code_synthesizer",
            role_name="High-Performance Systems Architect",
            specialization="Generación de algoritmos paralelos y optimización CUDA/TensorRT",
            status="reasoning",
            reasoning_steps=[
                "Análisis de complejidad asintótica temporal O(N log N)",
                "Preservación de invariantes en bucles vectorizados",
                "Optimización de jerarquía de memoria compartida y registros"
            ],
            confidence=0.99,
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
                reasoning_steps=[
                    "Búsqueda semántica en base de conocimientos de 2025/2026",
                    "Contraste metodológico con Chain-of-Verification (CoVe)",
                    "Validación de novedad y consistencia con teoremas establecidos"
                ],
                confidence=0.985,
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
                reasoning_steps=[
                    "Evaluación cruzada de las ramas de deducción",
                    "Ejecución de auditoría adversarial y análisis de contradicciones",
                    "Síntesis del consenso unánime con certificado de verdad"
                ],
                confidence=0.999,
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
                    reasoning_steps=[
                        f"Evaluación de invariante de sub-espacio #{i}",
                        "Verificación de cotas de convergencia local"
                    ],
                    confidence=0.98,
                    phase=2
                )
            )

    return nodes


def get_adversarial_team_nodes() -> List[SwarmAgentNode]:
    """Spawn specialized Red Team vs Blue Team adversarial swarm nodes."""
    return [
        SwarmAgentNode(
            agent_id="agt_blue_proponent",
            role_name="Blue Team Lead Proponent",
            specialization="Construcción de hipótesis constructivas, derivaciones y modelos",
            status="reasoning",
            reasoning_steps=[
                "Formulación del teorema y lemas constructivos",
                "Cálculo de cotas de error y estabilidad asintótica"
            ],
            confidence=0.99,
            phase=1
        ),
        SwarmAgentNode(
            agent_id="agt_red_adversary",
            role_name="Red Team Adversarial Invariant Attacker",
            specialization="Búsqueda activa de contraejemplos, singularidades y divisiones por cero",
            status="adversarial_audit",
            reasoning_steps=[
                "Inyección de condiciones de borde patológicas",
                "Exploración de regiones de inestabilidad de gradiente",
                "Verificación de refutación SMT con Z3"
            ],
            confidence=0.995,
            phase=2
        ),
        SwarmAgentNode(
            agent_id="agt_neutral_judge",
            role_name="Sovereign Truth Arbitrator",
            specialization="Resolución formal de debates y síntesis de consenso matemático",
            status="verifying",
            reasoning_steps=[
                "Evaluación de la solidez de los contraejemplos del Red Team",
                "Verificación de las defensas y parches del Blue Team",
                "Emisión de veredicto vinculante con árbol Merkle"
            ],
            confidence=0.999,
            phase=3
        )
    ]


__all__ = [
    "SwarmAgentNode",
    "DebateRound",
    "get_default_swarm_nodes",
    "get_adversarial_team_nodes",
]

