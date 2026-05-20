TruthGPT ha sido mejorado con la técnica **Hallucination-focused Preference Optimization** (arXiv:2501.17295, Tang et al., 2025, NAACL 2025 Main Conference). Se ha creado el archivo `/workspace/truthgpt_hallucination_focused_po.py` y se ha añadido al registro de técnicas. Ahora TruthGPT integra **12 técnicas SOTA** de mitigación de alucinaciones:

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
12. **Hallucination-focused Preference Optimization** (arXiv:2501.17295) — nuevo

Esta técnica reduce alucinaciones en traducción automática en un 96% promedio al generar datasets de preferencia enfocados en alucinaciones y fine-tuning intrínseco.

¿Desea que implemente más técnicas recientes como *Self-Reflection* (arXiv:2402.11560), *Code as Reward* (arXiv:2405.16642) o *AutoAlign* (arXiv:2405.15542)?