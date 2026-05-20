TruthGPT ha sido mejorado con la integración completa de **Phase-wise Self-Reward Decoding** (arXiv:2604.17982, Liu et al., 2026). Esta técnica, originalmente multimodal, ha sido adaptada para texto y mitiga alucinaciones mediante un proceso iterativo de autorecompensa en fases. Se ha creado el archivo `/workspace/truthgpt_phase_self_reward.py` y se ha añadido la entrada `'phase_self_reward'` al `TECHNIQUE_REGISTRY` en `/workspace/truthgpt_unified.py` (versión 2.6).

**Técnicas SOTA disponibles (14):**
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
13. Hallucination-focused PO (arXiv:2501.17295)
14. **Phase-wise Self-Reward** (arXiv:2604.17982) — nueva

**Uso:** `agent.mitigate(technique='phase_self_reward', prompt=..., response=..., llm_callable=...)`

**Fuente verificable:** [arXiv:2604.17982](https://arxiv.org/abs/2604.17982)