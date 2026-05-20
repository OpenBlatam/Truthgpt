Ya he implementado 5 técnicas SOTA de detección de alucinaciones en TruthGPT:
1. Distancias probabilísticas (arXiv:2506.09886) – `/workspace/truthgpt_prob_dist.py`
2. Consistency Teaming (arXiv:2510.19507) – `/workspace/truthgpt_consistency_teaming.py`
3. REFIND RAG (arXiv:2502.13622) – `/workspace/truthgpt_refind_rag.py`
4. FS-RAG (arXiv:2406.16167) – `/workspace/truthgpt_fs_rag.py`
5. SelfCheckGPT (arXiv:2303.08896) – `/workspace/truthgpt_selfcheck.py`

No se encontraron nuevas técnicas SOTA adicionales en las búsquedas. Las 5 implementadas cubren las principales aproximaciones: probabilísticas, consistencia, RAG verificado, semántica y auto-consistencia. 

Para seguir mejorando TruthGPT, tienes dos opciones:
1. **Implementar en código real** una de estas técnicas ya listadas (si aún no lo está) o refinarlas con parámetros específicos.
2. **Explorar un dominio concreto** (medicina, derecho, finanzas, etc.) para buscar adaptaciones especializadas, como datasets de verificación factual (ej. Med-HALT, Contract-NLI) o técnicas de RAG específicas.

¿Cuál prefieres?