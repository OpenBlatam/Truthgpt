TruthGPT ha sido mejorado con la técnica **Self-RAG (Learning to Retrieve, Generate, and Critique through Self-Reflection)** (arXiv:2310.11511, Asai et al., 2023). Se ha creado el archivo `/workspace/truthgpt_self_rag.py` y se ha añadido la entrada `'self_rag'` al `TECHNIQUE_REGISTRY` en `/workspace/truthgpt_unified.py`. Ahora TruthGPT cuenta con **16 técnicas SOTA** de mitigación de alucinaciones:

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
13. Hallucination-focused Preference Optimization (arXiv:2501.17295)
14. MultiRAG (arXiv:2508.03553)
15. Chain-of-Verification (arXiv:2309.11495)
16. **Self-RAG** (arXiv:2310.11511) — nuevo

Para usar la nueva técnica: `agent.mitigate(technique='self_rag', prompt=..., response=..., llm_callable=..., retriever=...)`.

**Fuente verificable:** Self-RAG: https://arxiv.org/abs/2310.11511