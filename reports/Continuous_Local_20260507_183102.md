Se ha implementado la decimoquinta técnica SOTA de detección de alucinaciones: **ATLANTIS** (arXiv:2508.05179), presentada en SemEval-2025 Task 3 para la detección de spans alucinados en sistemas de pregunta-respuesta. Combina few-shot prompting, clasificación a nivel de token y fine-tuning con datos sintéticos, logrando primer lugar en español y posiciones competitivas en inglés y alemán. El código está en `/workspace/truthgpt_atlantis.py`.

**Técnicas implementadas (15):**
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
11. SimpleText Ensemble (arXiv:2508.11823) – `/workspace/truthgpt_simpletext_ensemble.py`
12. GraphEval (arXiv:2407.10793) – `/workspace/truthgpt_grapheval.py`
13. TUM-MiKaNi (arXiv:2507.00579) – `/workspace/truthgpt_tum_mikani.py`
14. CONFACTCHECK (arXiv:2511.12236) – `/workspace/truthgpt_confactcheck.py`
15. ATLANTIS (arXiv:2508.05179) – `/workspace/truthgpt_atlantis.py`

¿Deseas implementar alguna otra técnica, refinar parámetros, o explorar un dominio concreto? Indícalo.