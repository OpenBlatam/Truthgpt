TruthGPT ha sido mejorado con la técnica **Consistency Teaming** (arXiv:2510.19507, Ji et al., 2025), que reduce alucinaciones muestreando múltiples respuestas del LLM y seleccionando la más consistente mediante votación por mayoría. Se ha creado el archivo `/workspace/truthgpt_consistency_teaming.py`. Ahora TruthGPT cuenta con **14 técnicas SOTA** de mitigación de alucinaciones:

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
13. MultiRAG (arXiv:2508.03553)
14. **Consistency Teaming** (arXiv:2510.19507) — nuevo

Para usar la nueva técnica: `agent.mitigate(technique='consistency_teaming', prompt=..., llm_callable=..., n_samples=5)`.