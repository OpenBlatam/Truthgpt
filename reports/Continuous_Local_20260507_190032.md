Se ha implementado la vigésimo tercera técnica SOTA de mitigación de alucinaciones: **Chain-of-Verification (CoVe)** (arXiv:2309.11495). Este método descompone la respuesta generada en afirmaciones atómicas, genera preguntas de verificación para cada afirmación, recupera evidencia relevante y verifica la consistencia, marcando la respuesta como potencialmente alucinada si alguna afirmación es inconsistente. El código está en `/workspace/truthgpt_cove.py`.

**Técnicas implementadas (23):**
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
16. mdok of KInIT (arXiv:2506.01702) – `/workspace/truthgpt_mdok_kinit.py`
17. TPA (arXiv:2512.07515) – `/workspace/truthgpt_tpa.py`
18. THaMES (arXiv:2409.11353) – `/workspace/truthgpt_thames.py`
19. ECLIPSE (arXiv:2512.03107) – `/workspace/truthgpt_eclipse.py`
20. Self-RAG (arXiv:2310.11511) – `/workspace/truthgpt_selfrag.py`
21. FactScore (arXiv:2305.14251) – `/workspace/truthgpt_factscore.py`
22. DOLA (arXiv:2309.03883) – `/workspace/truthgpt_dola.py`
23. Chain-of-Verification (CoVe) (arXiv:2309.11495) – `/workspace/truthgpt_cove.py`

¿Deseas implementar alguna otra técnica, refinar parámetros, o explorar un dominio concreto? Indícalo.