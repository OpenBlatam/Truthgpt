TruthGPT ha sido mejorado con la técnica **Self-Reflection** (arXiv:2310.06271, Madaan et al., 2024), que reduce alucinaciones mediante un proceso de dos pasos: generar una respuesta inicial y luego reflexionar sobre ella para refinarla. Se ha creado el archivo `/workspace/truthgpt_self_reflection.py` y se ha integrado en `/workspace/truthgpt_unified.py` (versión 2.4). Ahora TruthGPT cuenta con **12 técnicas SOTA** de mitigación de alucinaciones:

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
12. **Self-Reflection** (arXiv:2310.06271) — nuevo

Para usar la nueva técnica: `agent.mitigate(technique='self_reflection', prompt=..., response=...)`.