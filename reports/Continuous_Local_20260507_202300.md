TruthGPT ha sido mejorado con la técnica **SPIN (Self-Play Fine-Tuning)** (arXiv:2401.01335, Chen et al., 2024). Se ha creado el archivo `/workspace/truthgpt_spin.py` y se ha registrado en la última versión (2.3) de `/workspace/truthgpt_unified.py`. Ahora TruthGPT integra **11 técnicas SOTA** de mitigación de alucinaciones:

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
11. **SPIN** (arXiv:2401.01335) — nuevo

SPIN mejora la veracidad mediante un mecanismo de auto-juego iterativo: el modelo genera respuestas, las juzga contra una referencia y se ajusta gradualmente, reduciendo alucinaciones factuales. Para usarlo: `agent.mitigate(technique='spin', prompt=..., response=...)`.