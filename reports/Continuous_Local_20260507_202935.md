TruthGPT ha sido mejorado con la técnica **MultiRAG** (arXiv:2508.03553, Wu et al., 2025, aceptado en ICDE 2025), un framework guiado por conocimiento para mitigar alucinaciones en generación aumentada por recuperación multi-fuente. Se ha creado el archivo `/workspace/truthgpt_multir.py` y se ha integrado en el kernel. MultiRAG introduce dos innovaciones clave: (1) un módulo de construcción de conocimiento basado en grafos de líneas multi-fuente para agregar relaciones lógicas entre fuentes; (2) un módulo de recuperación con cálculo de confianza multinivel (a nivel de grafo y de nodo) para eliminar nodos no fiables. Esta técnica mejora la fiabilidad en escenarios complejos con múltiples fuentes de información.

Ahora TruthGPT cuenta con **13 técnicas SOTA** de mitigación de alucinaciones:
1. DoLA (arXiv:2309.03883)
2. Constitutional AI (arXiv:2212.08073)
3. ORPO (arXiv:2403.07691)
4. Self-Rewarding (arXiv:2401.10020)
5. Self-Consistency (arXiv:2203.11171)
6. Semantic Entropy (arXiv:2306.04786)
7. FS-RAG (arXiv:2406.16167)
8. REFIND RAG (arXiv:2502.13622)
9. Contrastive Decoding (arXiv:2210.15097)
10. DPO (arXiv:2305.18290)
11. SPIN (arXiv:2401.01335)
12. Self-Reflection (arXiv:2310.06271)
13. **MultiRAG** (arXiv:2508.03553) — nuevo

Para usarla: `agent.mitigate(technique='multir', query=..., sources=..., llm_callable=...)`.