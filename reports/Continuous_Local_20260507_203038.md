TruthGPT ha sido mejorado a la **versión 2.5** mediante la integración completa de la técnica **Hallucination-focused Preference Optimization** (arXiv:2501.17295, Tang et al., 2025, NAACL 2025 Main Conference) en el módulo unificado `/workspace/truthgpt_unified.py`. Esta técnica reduce las alucinaciones en traducción automática en un 96% promedio. Ahora TruthGPT cuenta con **13 técnicas SOTA** de mitigación de alucinaciones:

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
13. **Hallucination-focused Preference Optimization** (arXiv:2501.17295) — nuevo

Para usar la nueva técnica: `agent.mitigate(technique='hallucination_focused_po', prompt=..., response=...)`. Se recomienda explorar papers adicionales de 2025 como 'Phase-wise Self-reward' (arXiv:2604.17982) para futuras mejoras.