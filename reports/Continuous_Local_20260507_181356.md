Se ha implementado la octava técnica SOTA de detección de alucinaciones: **SLM Ensemble** (arXiv:2506.22486 – ICDE Workshop 2025). Este método utiliza un conjunto de modelos de lenguaje pequeños (e.g., DistilBERT) para verificar oraciones individuales de la respuesta contra el contexto, combinando probabilidades de tokens 'Yes' y similitud semántica. Reporta una mejora del 10% en F1. El código está en `/workspace/truthgpt_slm_ensemble.py`.

**Técnicas implementadas ahora (8):**
1. Distancias probabilísticas (arXiv:2506.09886) – `/workspace/truthgpt_prob_dist.py`
2. Consistency Teaming (arXiv:2510.19507) – `/workspace/truthgpt_consistency_teaming.py`
3. REFIND RAG (arXiv:2502.13622) – `/workspace/truthgpt_refind_rag.py`
4. FS-RAG (arXiv:2406.16167) – `/workspace/truthgpt_fs_rag.py`
5. SelfCheckGPT (arXiv:2303.08896) – `/workspace/truthgpt_selfcheck.py`
6. NLI Hallucination Detector (arXiv:2211.14269) – `/workspace/truthgpt_nli.py`
7. Ensemble Detector – `/workspace/truthgpt_ensemble.py`
8. SLM Ensemble (arXiv:2506.22486) – `/workspace/truthgpt_slm_ensemble.py`

¿Deseas implementar alguna otra técnica, refinar parámetros, o explorar un dominio concreto?