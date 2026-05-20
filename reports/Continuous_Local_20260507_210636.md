TruthGPT ha sido mejorado. Tras revisar las últimas publicaciones de arXiv, se han integrado dos nuevas técnicas SOTA de mitigación de alucinaciones:

1. **Generation Constraint Scaling** (arXiv:2407.16908, ICML 2024 Workshop): Método training-free que escala el vector de restricción en decodificadores con memoria para mitigar alucinaciones. Supera a métodos de edición en calidad y velocidad.

2. **Counterfactual Probing** (arXiv:2508.01862, 2025): Genera afirmaciones contrafácticas sutiles para evaluar la sensibilidad del modelo y corregir alucinaciones sin reentrenamiento. Reduce alucinaciones un 24.5% en benchmarks.

Ahora el kernel de TruthGPT cuenta con **25 técnicas** verificadas. Técnicas adicionales disponibles:
- DoLA (2309.03883)
- Constitutional AI (2212.08073)
- ORPO (2403.07691)
- Self-Rewarding (2401.10020)
- Self-Consistency (2203.11171)
- Semantic Entropy (2306.04786)
- FS-RAG (2406.16167)
- REFIND RAG (2502.13622)
- Contrastive Decoding (2210.15097)
- DPO (2305.18290)
- SPIN (2401.01335)
- Self-Reflection (2310.06271)
- Hallucination-focused PO (2501.17295)
- Phase-wise Self-Reward (2604.17982)
- APASI (2509.11287)
- Consistency Teaming (2510.19507)
- MultiRAG (2508.03553)
- Chain-of-Verification (2309.11495)
- Self-RAG (2310.11511)
- LANCET (2404.01697)
- Probabilistic Distance Detection (2506.09886)
- THaMES (2409.11353)
- Hallucination Detection with SLMs (2506.22486)

Se recomienda monitorear arXiv cs.CL diariamente para futuras novedades.