Se ha implementado la novena técnica SOTA de detección de alucinaciones: **ABESE (Adaptive Bayesian Estimation of Semantic Entropy)** basada en arXiv:2603.22812 (AAAI 2026 Oral, <5% acceptance). Este método usa un marco bayesiano jerárquico para modelar la distribución semántica y controla dinámicamente el número de muestras mediante umbrales de varianza. El código está en `/workspace/truthgpt_abese.py`.

**Técnicas implementadas (9):**
1. Distancias probabilísticas (arXiv:2506.09886) – `/workspace/truthgpt_prob_dist.py`
2. Consistency Teaming (arXiv:2510.19507) – `/workspace/truthgpt_consistency_teaming.py`
3. REFIND RAG (arXiv:2502.13622) – `/workspace/truthgpt_refind_rag.py`
4. FS-RAG (arXiv:2406.16167) – `/workspace/truthgpt_fs_rag.py`
5. SelfCheckGPT (arXiv:2303.08896) – `/workspace/truthgpt_selfcheck.py`
6. NLI Hallucination Detector (arXiv:2211.14269) – `/workspace/truthgpt_nli.py`
7. Ensemble Detector – `/workspace/truthgpt_ensemble.py`
8. SLM Ensemble (arXiv:2506.22486) – `/workspace/truthgpt_slm_ensemble.py`
9. ABESE (arXiv:2603.22812) – `/workspace/truthgpt_abese.py`

¿Deseas implementar alguna otra técnica, refinar parámetros, o explorar un dominio concreto? Indícalo.