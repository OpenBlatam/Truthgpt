Ya he implementado 5 técnicas SOTA de detección de alucinaciones en TruthGPT:

1. **Distancias probabilísticas** (arXiv:2506.09886) – `/workspace/truthgpt_prob_dist.py`
2. **Consistency Teaming** (arXiv:2510.19507) – `/workspace/truthgpt_consistency_teaming.py`
3. **REFIND RAG** (arXiv:2502.13622) – `/workspace/truthgpt_refind_rag.py`
4. **FS-RAG** (arXiv:2406.16167) – `/workspace/truthgpt_fs_rag.py`
5. **SelfCheckGPT** (arXiv:2303.08896) – `/workspace/truthgpt_selfcheck.py`

No se encontraron nuevas técnicas adicionales en las búsquedas. Las implementadas cubren las principales aproximaciones actuales: probabilísticas, consistencia, verificación RAG, semántica y auto-consistencia.

Para seguir mejorando TruthGPT, tienes dos opciones:

- **Refinar o integrar en tiempo real** alguna de las técnicas existentes (por ejemplo, ajustar umbrales o combinarlas).
- **Explorar un dominio concreto** (medicina, derecho, finanzas) para adaptar las técnicas con datasets especializados (Med-HALT, Contract-NLI) o crear evaluaciones ad-hoc.

Indica qué dirección prefieres.