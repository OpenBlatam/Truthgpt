Se ha implementado la décima técnica SOTA de detección de alucinaciones: **UCSC SemEval-2025 Framework** (arXiv:2505.03030), #1 en Mu-SHROOM Task 3. Combina recuperación de contexto, tres métodos de detección (extracción directa, verificación con grafo de conocimiento, revisión de costo mínimo) y optimización automática de prompts. El código está en `/workspace/truthgpt_ucsc_semeval.py`.

**Técnicas implementadas (10):**
1. Distancias probabilísticas (arXiv:2506.09886) – `/workspace/truthgpt_prob_dist.py`
2. Consistency Teaming (arXiv:2510.19507) – `/workspace/truthgpt_consistency_teaming.py`
3. REFIND RAG (arXiv:2502.13622) – `/workspace/truthgpt_refind_rag.py`
4. FS-RAG (arXiv:2406.16167) – `/workspace/truthgpt_fs_rag.py`
5. SelfCheckGPT (arXiv:2303.08896) – `/workspace/truthgpt_selfcheck.py`
6. NLI Hallucination Detector (arXiv:2211.14269) – `/workspace/truthgpt_nli.py`
7. Ensemble Detector – `/workspace/truthgpt_ensemble.py`
8. SLM Ensemble (arXiv:2506.22486) – `/workspace/truthgpt_slm_ensemble.py`
9. ABESE (arXiv:2603.22812) – `/workspace/truthgpt_abese.py`
10. UCSC SemEval-2025 (arXiv:2505.03030) – `/workspace/truthgpt_ucsc_semeval.py`

¿Deseas implementar alguna otra técnica, refinar parámetros, o explorar un dominio concreto? Indícalo.